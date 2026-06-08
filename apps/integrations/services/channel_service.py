"""Channel account CRUD and local test message simulation."""
from apps.agents.models import AgentInstance
from apps.inbox.models import ChannelAccount, ChannelType
from apps.integrations.forms import ChannelAccountForm
from apps.integrations.models import ChannelCredential, WebhookEvent, WebhookProcessingStatus
from apps.integrations.services.channel_credentials import encrypt_value, mask_credential_value
from apps.integrations.services.credential_encryption import is_encrypted, rotate_secret_if_plain
from apps.tenants.audit import log_audit_event
from apps.integrations.services.message_pipeline import InboundMessageService
from apps.integrations.services.normalizers import NormalizedInboundMessage
from apps.integrations.services.webhook_logger import log_received, mark_event
from apps.tenants.models import Tenant


def create_channel_account(
    tenant: Tenant,
    form: ChannelAccountForm,
    *,
    user=None,
    request=None,
) -> ChannelAccount:
    data = form.cleaned_data
    account = ChannelAccount.objects.create(
        tenant=tenant,
        channel_type=data["channel_type"],
        display_name=data["display_name"],
        is_active=data.get("is_active", True),
        mock_mode=data.get("mock_mode", True),
    )
    _upsert_credential(tenant, account, data, is_create=True, user=user, request=request)
    return account


def update_channel_account(
    account: ChannelAccount,
    form: ChannelAccountForm,
    *,
    user=None,
    request=None,
) -> ChannelAccount:
    data = form.cleaned_data
    account.display_name = data["display_name"]
    account.is_active = data.get("is_active", True)
    account.mock_mode = data.get("mock_mode", True)
    account.save(update_fields=["display_name", "is_active", "mock_mode", "updated_at"])
    _upsert_credential(
        account.tenant, account, data, is_create=False, user=user, request=request
    )
    return account


def _upsert_credential(
    tenant: Tenant,
    account: ChannelAccount,
    data: dict,
    *,
    is_create: bool = False,
    user=None,
    request=None,
) -> ChannelCredential:
    cred, created = ChannelCredential.objects.get_or_create(
        tenant=tenant,
        channel_account=account,
        defaults={"provider": "meta", "is_active": True},
    )
    cred.phone_number_id = data.get("phone_number_id", "")
    cred.page_id = data.get("instagram_page_id", "")
    cred.business_account_id = data.get("business_account_id", "")
    cred.verify_token = data.get("verify_token") or "ai-agent-os-verify"
    token_updated = False
    if data.get("access_token"):
        cred.access_token_encrypted = encrypt_value(data["access_token"])
        token_updated = True
    elif cred.access_token_encrypted:
        cred.access_token_encrypted = rotate_secret_if_plain(cred.access_token_encrypted)
    if data.get("app_secret"):
        cred.app_secret_encrypted = encrypt_value(data["app_secret"])
        token_updated = True
    elif cred.app_secret_encrypted:
        cred.app_secret_encrypted = rotate_secret_if_plain(cred.app_secret_encrypted)
    cred.is_active = data.get("is_active", True)
    cred.save()

    action = "integration_credential_create" if (is_create or created) else "integration_credential_update"
    log_audit_event(
        action=action,
        tenant=tenant,
        user=user,
        object_type="channel_credential",
        object_id=cred.pk,
        metadata={
            "channel_type": account.channel_type,
            "display_name": account.display_name,
            "token_updated": token_updated,
            "access_token_masked": mask_credential_value(cred.access_token_encrypted),
            "encrypted": is_encrypted(cred.access_token_encrypted) if cred.access_token_encrypted else None,
        },
        request=request,
    )
    return cred


def toggle_channel_active(account: ChannelAccount) -> ChannelAccount:
    account.is_active = not account.is_active
    account.save(update_fields=["is_active", "updated_at"])
    if hasattr(account, "credential"):
        account.credential.is_active = account.is_active
        account.credential.save(update_fields=["is_active", "updated_at"])
    return account


def account_form_initial(account: ChannelAccount) -> dict:
    cred = getattr(account, "credential", None)
    return {
        "channel_type": account.channel_type,
        "display_name": account.display_name,
        "phone_number_id": cred.phone_number_id if cred else "",
        "business_account_id": cred.business_account_id if cred else "",
        "instagram_page_id": cred.page_id if cred else "",
        "verify_token": cred.verify_token if cred else "",
        "is_active": account.is_active,
        "mock_mode": account.mock_mode,
    }


def get_last_webhook_event(account: ChannelAccount) -> WebhookEvent | None:
    cred = getattr(account, "credential", None)
    if not cred:
        return None
    qs = WebhookEvent.objects.filter(tenant=account.tenant, channel_type=account.channel_type)
    if account.channel_type == ChannelType.WHATSAPP and cred.phone_number_id:
        qs = qs.filter(normalized_json__metadata__phone_number_id=cred.phone_number_id)
    elif account.channel_type == ChannelType.INSTAGRAM and cred.page_id:
        qs = qs.filter(normalized_json__metadata__page_id=cred.page_id)
    return qs.order_by("-received_at").first()


def simulate_test_message(
    tenant: Tenant,
    account: ChannelAccount,
    *,
    message_text: str,
    customer_name: str,
    customer_phone: str = "",
    customer_username: str = "",
    agent_instance: AgentInstance,
) -> dict:
    """Simulate inbound webhook message and route through full pipeline."""
    channel_type = account.channel_type
    external_id = f"test_{account.pk}_{WebhookEvent.objects.count() + 1}"
    cred = getattr(account, "credential", None)

    normalized = NormalizedInboundMessage(
        channel_type=channel_type,
        external_message_id=external_id,
        external_conversation_id=f"conv_{external_id}",
        external_contact_id=customer_phone or customer_username or "test_contact",
        sender_name=customer_name,
        sender_phone=customer_phone,
        sender_username=customer_username,
        message_text=message_text,
        message_type="text",
        timestamp=None,
        raw_payload={"simulated": True, "channel_account_id": account.pk},
        metadata={
            "phone_number_id": cred.phone_number_id if cred else "",
            "page_id": cred.page_id if cred else "",
            "simulated": True,
        },
    )

    event = log_received(
        channel_type,
        normalized.raw_payload,
        tenant=tenant,
        external_message_id=external_id,
        event_type="simulated_test",
    )
    event.normalized_json = normalized.to_dict()
    event.save(update_fields=["normalized_json"])

    try:
        result = InboundMessageService.process(
            tenant,
            message_text=message_text,
            channel_type=channel_type,
            customer_name=customer_name,
            customer_phone=customer_phone or customer_username,
            agent_instance=agent_instance,
            session_key=f"test_{account.pk}_{external_id}",
            metadata={"provider": "simulator", "channel_account_id": account.pk},
        )
        event.conversation_id = result.conversation_id
        mark_event(event, WebhookProcessingStatus.PROCESSED)
        return {
            "success": True,
            "conversation_id": result.conversation_id,
            "ai_reply": result.ai_reply,
            "lead_id": result.lead_id,
            "agent_run_id": result.agent_run_id,
            "intent": result.intent,
            "webhook_event_id": event.pk,
        }
    except Exception as exc:
        mark_event(event, WebhookProcessingStatus.FAILED, error_message=str(exc))
        return {"success": False, "error": str(exc), "webhook_event_id": event.pk}
