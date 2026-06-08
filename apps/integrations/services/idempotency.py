"""Webhook message deduplication."""
import hashlib

from apps.inbox.models import Message
from apps.integrations.models import WebhookEvent, WebhookProcessingStatus


def build_fallback_message_id(channel_type: str, sender: str, timestamp: str, text: str) -> str:
    raw = f"{channel_type}:{sender}:{timestamp}:{text}"
    return hashlib.sha256(raw.encode()).hexdigest()


def get_message_id(normalized: dict) -> str:
    external_id = normalized.get("external_message_id", "")
    if external_id:
        return external_id
    return build_fallback_message_id(
        normalized.get("channel_type", ""),
        normalized.get("external_contact_id", ""),
        normalized.get("timestamp", ""),
        normalized.get("message_text", ""),
    )


def is_duplicate_message(channel_type: str, external_message_id: str) -> bool:
    if WebhookEvent.objects.filter(
        channel_type=channel_type,
        external_message_id=external_message_id,
        processing_status=WebhookProcessingStatus.PROCESSED,
    ).exists():
        return True
    return Message.objects.filter(
        metadata_json__external_message_id=external_message_id,
        metadata_json__channel_type=channel_type,
    ).exists()
