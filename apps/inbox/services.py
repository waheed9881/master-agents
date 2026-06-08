"""Inbox message and conversation services."""
import uuid

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

from apps.agents.models import AgentInstance
from apps.crm.models import Contact
from apps.crm.services import create_contact
from apps.inbox.models import (
    ChannelType,
    Conversation,
    ConversationStatus,
    Message,
    SenderType,
)
from apps.tenants.models import Tenant


def create_message(
    conversation: Conversation,
    *,
    sender_type: str,
    message_text: str,
    metadata: dict | None = None,
) -> Message:
    """Save a message and update conversation timestamp."""
    message = Message.objects.create(
        conversation=conversation,
        sender_type=sender_type,
        message_text=message_text,
        metadata_json=metadata or {},
    )
    conversation.last_message_at = timezone.now()
    conversation.save(update_fields=["last_message_at", "updated_at"])
    broadcast_message(conversation, message)
    return message


def find_or_create_contact(
    tenant: Tenant,
    *,
    name: str,
    email: str = "",
    phone: str = "",
    source: str = "web_chat",
) -> Contact:
    if email:
        contact = Contact.objects.filter(tenant=tenant, email=email).first()
        if contact:
            if name and contact.name != name:
                contact.name = name
                contact.save(update_fields=["name", "updated_at"])
            return contact
    if phone:
        contact = Contact.objects.filter(tenant=tenant, phone=phone).first()
        if contact:
            return contact
    return create_contact(
        tenant,
        name=name or "Web Chat Visitor",
        email=email,
        phone=phone,
        source=source,
    )


def find_or_create_conversation(
    tenant: Tenant,
    contact: Contact,
    *,
    channel_type: str = ChannelType.WEB_CHAT,
    agent_instance: AgentInstance | None = None,
    session_key: str = "",
) -> Conversation:
    from apps.inbox.selectors import find_open_conversation

    existing = find_open_conversation(
        tenant,
        session_key=session_key,
        contact_id=contact.pk,
        channel_type=channel_type,
        agent_instance_id=agent_instance.pk if agent_instance else None,
    )
    if existing:
        return existing

    if not session_key:
        session_key = str(uuid.uuid4())

    return Conversation.objects.create(
        tenant=tenant,
        contact=contact,
        agent_instance=agent_instance,
        channel_type=channel_type,
        status=ConversationStatus.OPEN,
        session_key=session_key,
    )


def enable_human_takeover(conversation: Conversation, *, user=None, request=None) -> Conversation:
    conversation.human_takeover = True
    conversation.ai_enabled = False
    conversation.save(update_fields=["human_takeover", "ai_enabled", "updated_at"])
    create_message(
        conversation,
        sender_type=SenderType.SYSTEM,
        message_text="A human agent will take over this conversation shortly.",
    )
    from apps.tenants.audit import log_audit_event

    log_audit_event(
        action="human_handoff_toggle",
        tenant=conversation.tenant,
        user=user,
        object_type="conversation",
        object_id=conversation.pk,
        metadata={"enabled": True},
        request=request,
    )
    return conversation


def enable_ai(conversation: Conversation) -> Conversation:
    conversation.human_takeover = False
    conversation.ai_enabled = True
    conversation.save(update_fields=["human_takeover", "ai_enabled", "updated_at"])
    create_message(
        conversation,
        sender_type=SenderType.SYSTEM,
        message_text="AI assistant has been re-enabled for this conversation.",
    )
    return conversation


def send_human_reply(conversation: Conversation, message_text: str, user) -> Message:
    return create_message(
        conversation,
        sender_type=SenderType.HUMAN,
        message_text=message_text,
        metadata={"user_id": user.pk},
    )


def broadcast_message(conversation: Conversation, message: Message) -> None:
    """Push message to WebSocket subscribers."""
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    room = f"inbox_{conversation.tenant_id}"
    async_to_sync(channel_layer.group_send)(
        room,
        {
            "type": "inbox.message",
            "conversation_id": conversation.pk,
            "message": {
                "id": message.pk,
                "sender_type": message.sender_type,
                "message_text": message.message_text,
                "created_at": message.created_at.isoformat(),
            },
        },
    )


def generate_stub_ai_reply(customer_message: str, conversation: Conversation) -> str:
    """
    Deterministic stub reply for Phase 4 demo.
    Replaced by SalesClosingAgent in Phase 5.
    """
    text = customer_message.lower()
    business = "our team"
    if conversation.agent_instance and hasattr(conversation.agent_instance, "settings"):
        settings = getattr(conversation.agent_instance, "settings", None)
        if settings and settings.business_name:
            business = settings.business_name

    if any(w in text for w in ("price", "cost", "pricing", "how much")):
        return (
            f"Thanks for asking about pricing! I'd be happy to help. "
            f"Could you share your budget range so I can recommend the best option from {business}?"
        )
    if any(w in text for w in ("demo", "call", "meeting", "schedule")):
        return (
            "Great — I'd love to set up a call or demo for you! "
            "What day and time works best, and what's the best number or email to reach you?"
        )
    if any(w in text for w in ("human", "person", "agent", "speak to")):
        return (
            "Of course — I'll connect you with a team member. "
            "Could you briefly describe what you need help with?"
        )
    if any(w in text for w in ("hello", "hi", "hey", "salam", "assalam")):
        return (
            f"Hello! Welcome to {business}. I'm here to help you find the right solution. "
            "What service are you looking for?"
        )
    return (
        "Thanks for your message! To help you better, could you tell me: "
        "1) What service are you looking for? "
        "2) What type of business do you have? "
        "3) What's your timeline?"
    )
