"""Normalize channel-specific webhook payloads into a common structure."""
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class NormalizedInboundMessage:
    channel_type: str
    external_message_id: str
    external_conversation_id: str = ""
    external_contact_id: str = ""
    sender_name: str = ""
    sender_phone: str = ""
    sender_username: str = ""
    message_text: str = ""
    message_type: str = "text"
    timestamp: str = ""
    raw_payload: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def normalize_whatsapp_payload(payload: dict) -> list[NormalizedInboundMessage]:
    """Parse WhatsApp Cloud API-style webhook payload."""
    results: list[NormalizedInboundMessage] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            metadata = value.get("metadata", {})
            phone_number_id = metadata.get("phone_number_id", "")
            contacts = {c.get("wa_id", ""): c for c in value.get("contacts", [])}

            for message in value.get("messages", []):
                msg_type = message.get("type", "text")
                external_id = message.get("id", "")
                sender = message.get("from", "")
                contact = contacts.get(sender, {})
                profile_name = contact.get("profile", {}).get("name", "")
                text_body = ""
                if msg_type == "text":
                    text_body = message.get("text", {}).get("body", "")
                results.append(
                    NormalizedInboundMessage(
                        channel_type="whatsapp",
                        external_message_id=external_id,
                        external_conversation_id=sender,
                        external_contact_id=sender,
                        sender_name=profile_name or sender,
                        sender_phone=sender,
                        message_text=text_body,
                        message_type=msg_type,
                        timestamp=str(message.get("timestamp", "")),
                        raw_payload=message,
                        metadata={
                            "phone_number_id": phone_number_id,
                            "waba_id": entry.get("id", ""),
                            "field": change.get("field", ""),
                        },
                    )
                )
    return results


def normalize_instagram_payload(payload: dict) -> list[NormalizedInboundMessage]:
    """Parse Instagram Messaging webhook payload."""
    results: list[NormalizedInboundMessage] = []
    for entry in payload.get("entry", []):
        page_id = str(entry.get("id", ""))
        for event in entry.get("messaging", []):
            message = event.get("message", {})
            if not message:
                continue
            sender = event.get("sender", {})
            recipient = event.get("recipient", {})
            msg_type = "text" if "text" in message else message.get("type", "unknown")
            text_body = message.get("text", "") if isinstance(message.get("text"), str) else message.get("text", {}).get("body", "")
            results.append(
                NormalizedInboundMessage(
                    channel_type="instagram",
                    external_message_id=message.get("mid", ""),
                    external_conversation_id=sender.get("id", ""),
                    external_contact_id=sender.get("id", ""),
                    sender_name=sender.get("id", "Instagram User"),
                    sender_username=sender.get("id", ""),
                    message_text=text_body,
                    message_type=msg_type,
                    timestamp=str(event.get("timestamp", "")),
                    raw_payload=event,
                    metadata={
                        "page_id": page_id,
                        "recipient_id": recipient.get("id", ""),
                    },
                )
            )
    return results


def normalize_payload(channel_type: str, payload: dict) -> list[NormalizedInboundMessage]:
    if channel_type == "whatsapp":
        return normalize_whatsapp_payload(payload)
    if channel_type == "instagram":
        return normalize_instagram_payload(payload)
    return []
