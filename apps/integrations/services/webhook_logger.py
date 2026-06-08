"""Webhook event logging."""
from django.utils import timezone

from apps.integrations.models import WebhookEvent, WebhookProcessingStatus
from apps.tenants.models import Tenant


def log_received(
    channel_type: str,
    payload: dict,
    *,
    tenant: Tenant | None = None,
    external_event_id: str = "",
    external_message_id: str = "",
    event_type: str = "message",
) -> WebhookEvent:
    return WebhookEvent.objects.create(
        tenant=tenant,
        channel_type=channel_type,
        external_event_id=external_event_id,
        external_message_id=external_message_id,
        event_type=event_type,
        payload_json=payload,
        processing_status=WebhookProcessingStatus.RECEIVED,
    )


def mark_event(event: WebhookEvent, status: str, **kwargs) -> WebhookEvent:
    event.processing_status = status
    for key, value in kwargs.items():
        setattr(event, key, value)
    if status in (WebhookProcessingStatus.PROCESSED, WebhookProcessingStatus.IGNORED, WebhookProcessingStatus.DUPLICATE, WebhookProcessingStatus.FAILED):
        event.processed_at = timezone.now()
    event.save()
    return event
