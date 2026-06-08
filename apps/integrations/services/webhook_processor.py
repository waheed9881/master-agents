"""Process inbound webhooks end-to-end."""
import logging

from apps.inbox.models import ChannelType
from apps.integrations.models import WebhookProcessingStatus
from apps.integrations.services.channel_credentials import (
    get_active_agent_for_channel,
    resolve_tenant_for_instagram,
    resolve_tenant_for_whatsapp,
    should_enforce_signature,
    verify_meta_signature,
)
from apps.integrations.services.idempotency import get_message_id, is_duplicate_message
from apps.integrations.services.normalizers import normalize_payload
from apps.integrations.services.outbound import OutboundMessageService
from apps.integrations.services.webhook_logger import log_received, mark_event

logger = logging.getLogger(__name__)


class WebhookProcessorService:
    """Validate, normalize, dedupe, and route webhook payloads."""

    @classmethod
    def verify_subscription(cls, verify_token: str, challenge: str, mode: str) -> str | None:
        from django.conf import settings

        expected = getattr(settings, "META_VERIFY_TOKEN", "ai-agent-os-verify")
        if mode == "subscribe" and verify_token == expected:
            return challenge
        return None

    @classmethod
    def validate_signature(cls, raw_body: bytes, signature_header: str) -> bool:
        if not should_enforce_signature():
            return True
        return verify_meta_signature(raw_body, signature_header)

    @classmethod
    def process(cls, channel_type: str, payload: dict, raw_body: bytes = b"", signature: str = "") -> dict:
        if not cls.validate_signature(raw_body or str(payload).encode(), signature):
            return {"status": "forbidden", "error": "Invalid signature"}

        normalized_messages = normalize_payload(channel_type, payload)
        if not normalized_messages:
            event = log_received(channel_type, payload, event_type="empty")
            mark_event(event, WebhookProcessingStatus.IGNORED, error_message="No messages in payload")
            return {"status": "received", "processed": 0, "note": "No messages to process"}

        processed = 0
        duplicates = 0
        failed = 0

        for normalized in normalized_messages:
            norm_dict = normalized.to_dict()
            message_id = get_message_id(norm_dict)
            phone_number_id = norm_dict.get("metadata", {}).get("phone_number_id", "")
            page_id = norm_dict.get("metadata", {}).get("page_id", "")

            if channel_type == ChannelType.WHATSAPP:
                tenant, channel_account = resolve_tenant_for_whatsapp(phone_number_id)
            else:
                tenant, channel_account = resolve_tenant_for_instagram(page_id)

            event = log_received(
                channel_type,
                payload,
                tenant=tenant,
                external_message_id=message_id,
                event_type=norm_dict.get("message_type", "message"),
            )
            event.normalized_json = norm_dict
            event.save(update_fields=["normalized_json"])

            if not tenant:
                mark_event(event, WebhookProcessingStatus.FAILED, error_message="Tenant not resolved")
                failed += 1
                continue

            if norm_dict.get("message_type") != "text" or not norm_dict.get("message_text"):
                mark_event(
                    event,
                    WebhookProcessingStatus.IGNORED,
                    error_message=f"Unsupported type: {norm_dict.get('message_type')}",
                )
                continue

            if is_duplicate_message(channel_type, message_id):
                mark_event(event, WebhookProcessingStatus.DUPLICATE, error_message="Duplicate message")
                duplicates += 1
                continue

            try:
                result = cls._route_inbound(tenant, channel_account, norm_dict, event.pk)
                mark_event(event, WebhookProcessingStatus.PROCESSED)
                processed += 1
                if result.get("outbound"):
                    event.normalized_json = {**norm_dict, "outbound": result["outbound"]}
                    event.save(update_fields=["normalized_json"])
            except Exception as exc:
                logger.exception("Webhook processing failed")
                mark_event(event, WebhookProcessingStatus.FAILED, error_message=str(exc))
                failed += 1

        return {
            "status": "received",
            "processed": processed,
            "duplicates": duplicates,
            "failed": failed,
        }

    @classmethod
    def _route_inbound(cls, tenant, channel_account, norm_dict: dict, webhook_event_id: int) -> dict:
        from apps.integrations.services.message_pipeline import InboundMessageService

        agent = get_active_agent_for_channel(tenant, channel_account)
        session_key = f"{norm_dict['channel_type']}:{norm_dict['external_contact_id']}"

        metadata = {
            "external_message_id": norm_dict["external_message_id"],
            "external_conversation_id": norm_dict["external_conversation_id"],
            "external_contact_id": norm_dict["external_contact_id"],
            "provider": "meta",
            "channel_type": norm_dict["channel_type"],
            "webhook_event_id": webhook_event_id,
            "timestamp": norm_dict.get("timestamp", ""),
        }

        result = InboundMessageService.process(
            tenant,
            message_text=norm_dict["message_text"],
            channel_type=norm_dict["channel_type"],
            customer_name=norm_dict.get("sender_name") or "Channel Visitor",
            customer_phone=norm_dict.get("sender_phone", ""),
            agent_instance=agent,
            session_key=session_key,
            metadata=metadata,
        )

        outbound_result = None
        if result.ai_reply and norm_dict["channel_type"] in (ChannelType.WHATSAPP, ChannelType.INSTAGRAM):
            recipient = norm_dict.get("external_contact_id") or norm_dict.get("sender_phone", "")
            outbound_result = OutboundMessageService.send_message(
                channel_account,
                recipient,
                result.ai_reply,
                channel_type=norm_dict["channel_type"],
            )
            if result.ai_message_id:
                from apps.inbox.models import Message

                ai_msg = Message.objects.filter(pk=result.ai_message_id).first()
                if ai_msg:
                    ai_msg.metadata_json = {
                        **ai_msg.metadata_json,
                        "outbound": outbound_result,
                        "mock_mode": outbound_result.get("mock", True),
                    }
                    ai_msg.save(update_fields=["metadata_json"])

        return {"inbound": result, "outbound": outbound_result}
