"""Outbound message delivery for external channels."""
import logging
import uuid

import httpx
from django.conf import settings

from apps.inbox.models import ChannelAccount, ChannelType

logger = logging.getLogger(__name__)


class OutboundMessageService:
    """Send outbound messages via WhatsApp/Instagram APIs or mock mode."""

    @classmethod
    def send_message(
        cls,
        channel_account: ChannelAccount | None,
        recipient_id: str,
        text: str,
        *,
        channel_type: str = "",
    ) -> dict:
        channel = channel_type or (channel_account.channel_type if channel_account else "")
        if channel == ChannelType.WHATSAPP:
            return cls.send_whatsapp_message(channel_account, recipient_id, text)
        if channel == ChannelType.INSTAGRAM:
            return cls.send_instagram_message(channel_account, recipient_id, text)
        return cls.mock_send(channel or "unknown", recipient_id, text)

    @classmethod
    def send_whatsapp_message(
        cls,
        channel_account: ChannelAccount | None,
        recipient_phone: str,
        text: str,
    ) -> dict:
        if getattr(settings, "INTEGRATIONS_MOCK_MODE", True):
            return cls.mock_send(ChannelType.WHATSAPP, recipient_phone, text)

        from apps.integrations.services.channel_credentials import decrypt_value

        cred = getattr(channel_account, "credential", None) if channel_account else None
        token = decrypt_value(cred.access_token_encrypted) if cred else getattr(settings, "META_ACCESS_TOKEN", "")
        phone_number_id = cred.phone_number_id if cred else getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "")
        if not token or not phone_number_id:
            return cls.mock_send(ChannelType.WHATSAPP, recipient_phone, text)

        url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
        headers = {"Authorization": f"Bearer {token}"}
        body = {
            "messaging_product": "whatsapp",
            "to": recipient_phone,
            "type": "text",
            "text": {"body": text},
        }
        return cls._post_or_mock(url, headers, body, ChannelType.WHATSAPP, recipient_phone)

    @classmethod
    def send_instagram_message(
        cls,
        channel_account: ChannelAccount | None,
        recipient_id: str,
        text: str,
    ) -> dict:
        if getattr(settings, "INTEGRATIONS_MOCK_MODE", True):
            return cls.mock_send(ChannelType.INSTAGRAM, recipient_id, text)

        from apps.integrations.services.channel_credentials import decrypt_value

        cred = getattr(channel_account, "credential", None) if channel_account else None
        token = decrypt_value(cred.access_token_encrypted) if cred else getattr(settings, "META_ACCESS_TOKEN", "")
        page_id = cred.page_id if cred else getattr(settings, "INSTAGRAM_PAGE_ID", "")
        if not token or not page_id:
            return cls.mock_send(ChannelType.INSTAGRAM, recipient_id, text)

        url = f"https://graph.facebook.com/v19.0/{page_id}/messages"
        headers = {"Authorization": f"Bearer {token}"}
        body = {
            "recipient": {"id": recipient_id},
            "message": {"text": text},
        }
        return cls._post_or_mock(url, headers, body, ChannelType.INSTAGRAM, recipient_id)

    @classmethod
    def mock_send(cls, channel_type: str, recipient_id: str, text: str) -> dict:
        provider_id = f"mock_{channel_type}_{uuid.uuid4().hex[:12]}"
        logger.info(
            "Mock outbound %s to %s: %s",
            channel_type,
            recipient_id,
            text[:80],
        )
        return {
            "success": True,
            "mock": True,
            "provider_message_id": provider_id,
            "channel_type": channel_type,
            "recipient_id": recipient_id,
        }

    @classmethod
    def _post_or_mock(cls, url: str, headers: dict, body: dict, channel_type: str, recipient_id: str) -> dict:
        try:
            response = httpx.post(url, headers=headers, json=body, timeout=15.0)
            response.raise_for_status()
            data = response.json()
            messages = data.get("messages", [{}])
            provider_id = messages[0].get("id", "") if messages else data.get("message_id", "")
            return {
                "success": True,
                "mock": False,
                "provider_message_id": provider_id,
                "channel_type": channel_type,
                "recipient_id": recipient_id,
                "response": data,
            }
        except Exception as exc:
            logger.exception("Outbound send failed for %s", channel_type)
            return {
                "success": False,
                "mock": False,
                "error": str(exc),
                "channel_type": channel_type,
                "recipient_id": recipient_id,
            }
