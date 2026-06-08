"""Channel credential storage and tenant resolution."""
from django.conf import settings

from apps.inbox.models import ChannelAccount, ChannelType
from apps.integrations.models import ChannelCredential
from apps.tenants.models import Tenant


def encrypt_value(value: str) -> str:
    """Encrypt a secret value. Uses Fernet when key is configured."""
    if not value:
        return ""
    key = getattr(settings, "CREDENTIALS_ENCRYPTION_KEY", "")
    if not key:
        # TODO: require encryption in production
        return f"plain:{value}"
    try:
        from cryptography.fernet import Fernet

        return Fernet(key.encode() if isinstance(key, str) else key).encrypt(value.encode()).decode()
    except Exception:
        return f"plain:{value}"


def decrypt_value(encrypted: str) -> str:
    if not encrypted:
        return ""
    if encrypted.startswith("plain:"):
        return encrypted[6:]
    key = getattr(settings, "CREDENTIALS_ENCRYPTION_KEY", "")
    if not key:
        return ""
    try:
        from cryptography.fernet import Fernet

        return Fernet(key.encode() if isinstance(key, str) else key).decrypt(encrypted.encode()).decode()
    except Exception:
        return ""


def get_meta_app_secret() -> str:
    return getattr(settings, "META_APP_SECRET", "")


def verify_meta_signature(payload: bytes, signature_header: str) -> bool:
    """Validate X-Hub-Signature-256 from Meta webhooks."""
    import hashlib
    import hmac

    app_secret = get_meta_app_secret()
    if not app_secret or not signature_header:
        return False
    expected = "sha256=" + hmac.new(
        app_secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def should_enforce_signature() -> bool:
    mock_mode = getattr(settings, "INTEGRATIONS_MOCK_MODE", True)
    if mock_mode:
        return False
    return bool(get_meta_app_secret())


def resolve_tenant_for_whatsapp(phone_number_id: str) -> tuple[Tenant | None, ChannelAccount | None]:
    if phone_number_id:
        cred = (
            ChannelCredential.objects.filter(
                phone_number_id=phone_number_id,
                is_active=True,
                channel_account__channel_type=ChannelType.WHATSAPP,
            )
            .select_related("channel_account", "tenant")
            .first()
        )
        if cred:
            return cred.tenant, cred.channel_account

    return _demo_tenant_fallback()


def resolve_tenant_for_instagram(page_id: str) -> tuple[Tenant | None, ChannelAccount | None]:
    if page_id:
        cred = (
            ChannelCredential.objects.filter(
                page_id=page_id,
                is_active=True,
                channel_account__channel_type=ChannelType.INSTAGRAM,
            )
            .select_related("channel_account", "tenant")
            .first()
        )
        if cred:
            return cred.tenant, cred.channel_account

    return _demo_tenant_fallback()


def _demo_tenant_fallback() -> tuple[Tenant | None, ChannelAccount | None]:
    if not getattr(settings, "INTEGRATIONS_MOCK_MODE", True):
        return None, None
    tenants = Tenant.objects.all()
    if tenants.count() == 1:
        tenant = tenants.first()
        return tenant, None
    return Tenant.objects.filter(slug="demo-company").first(), None


def get_active_agent_for_channel(tenant: Tenant, channel_account: ChannelAccount | None):
    from apps.agents.models import AgentInstance

    return (
        AgentInstance.objects.filter(tenant=tenant, status="active")
        .select_related("template")
        .prefetch_related("settings")
        .first()
    )
