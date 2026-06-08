"""Inbox query helpers."""
from django.db.models import Count, QuerySet

from apps.inbox.models import Conversation, Message
from apps.tenants.models import Tenant


def list_tenant_conversations(tenant: Tenant) -> QuerySet[Conversation]:
    return (
        Conversation.objects.filter(tenant=tenant)
        .select_related("contact", "agent_instance")
        .prefetch_related("messages")
        .annotate(message_count=Count("messages"))
    )


def get_tenant_conversation(tenant: Tenant, conversation_id: int) -> Conversation | None:
    return (
        Conversation.objects.filter(tenant=tenant, pk=conversation_id)
        .select_related("contact", "agent_instance")
        .prefetch_related("messages")
        .first()
    )


def get_conversation_messages(conversation: Conversation) -> QuerySet[Message]:
    return conversation.messages.all().order_by("created_at")


def get_inbox_stats(tenant: Tenant) -> dict:
    conversations = Conversation.objects.filter(tenant=tenant)
    messages = Message.objects.filter(conversation__tenant=tenant)
    return {
        "total_conversations": conversations.count(),
        "open_conversations": conversations.filter(status="open").count(),
        "human_takeover_count": conversations.filter(human_takeover=True).count(),
        "ai_messages_sent": messages.filter(sender_type="ai").count(),
        "customer_messages": messages.filter(sender_type="customer").count(),
    }


def find_open_conversation(
    tenant: Tenant,
    *,
    session_key: str = "",
    contact_id: int | None = None,
    channel_type: str = "web_chat",
    agent_instance_id: int | None = None,
) -> Conversation | None:
    qs = Conversation.objects.filter(
        tenant=tenant,
        channel_type=channel_type,
        status="open",
    )
    if session_key:
        conv = qs.filter(session_key=session_key).first()
        if conv:
            return conv
    if contact_id and agent_instance_id:
        return qs.filter(contact_id=contact_id, agent_instance_id=agent_instance_id).first()
    return None
