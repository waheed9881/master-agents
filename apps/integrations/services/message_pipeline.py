"""Normalized inbound/outbound message processing."""
from dataclasses import dataclass

from apps.agent_engine.services.orchestrator import AgentOrchestrator
from apps.agents.models import AgentInstance
from apps.inbox.models import ChannelType, SenderType
from apps.inbox.services import (
    create_message,
    find_or_create_contact,
    find_or_create_conversation,
    generate_stub_ai_reply,
)
from apps.tenants.models import Tenant


@dataclass
class InboundMessageResult:
    conversation_id: int
    session_key: str
    contact_id: int
    customer_message_id: int
    ai_message_id: int | None
    ai_reply: str | None
    human_takeover: bool
    lead_id: int | None = None
    agent_run_id: int | None = None
    intent: str | None = None


class InboundMessageService:
    """Process inbound messages from any channel through a single pipeline."""

    IMPLEMENTED_SLUGS = {"sales-closing-agent"}

    @staticmethod
    def process(
        tenant: Tenant,
        *,
        message_text: str,
        channel_type: str = ChannelType.WEB_CHAT,
        customer_name: str = "Web Chat Visitor",
        customer_email: str = "",
        customer_phone: str = "",
        agent_instance: AgentInstance | None = None,
        session_key: str = "",
    ) -> InboundMessageResult:
        contact = find_or_create_contact(
            tenant,
            name=customer_name,
            email=customer_email,
            phone=customer_phone,
            source=channel_type,
        )
        conversation = find_or_create_conversation(
            tenant,
            contact,
            channel_type=channel_type,
            agent_instance=agent_instance,
            session_key=session_key,
        )

        customer_msg = create_message(
            conversation,
            sender_type=SenderType.CUSTOMER,
            message_text=message_text,
        )

        ai_message_id = None
        ai_reply = None
        lead_id = None
        agent_run_id = None
        intent = None

        if conversation.ai_enabled and not conversation.human_takeover and agent_instance:
            orchestrated = InboundMessageService._run_agent(
                agent_instance, conversation, message_text
            )
            if orchestrated:
                ai_reply = orchestrated.agent_result.reply
                lead_id = orchestrated.agent_result.lead_id
                agent_run_id = orchestrated.agent_run_id
                intent = orchestrated.agent_result.intent
                ai_msg = create_message(
                    conversation,
                    sender_type=SenderType.AI,
                    message_text=ai_reply,
                    metadata={
                        "engine": "agent_engine",
                        "intent": intent,
                        "lead_id": lead_id,
                        "agent_run_id": agent_run_id,
                        "handoff": orchestrated.agent_result.should_handoff,
                    },
                )
                ai_message_id = ai_msg.pk
                conversation.refresh_from_db()
            else:
                ai_reply = generate_stub_ai_reply(message_text, conversation)
                ai_msg = create_message(
                    conversation,
                    sender_type=SenderType.AI,
                    message_text=ai_reply,
                    metadata={"engine": "stub_fallback"},
                )
                ai_message_id = ai_msg.pk
        elif conversation.ai_enabled and not conversation.human_takeover:
            ai_reply = generate_stub_ai_reply(message_text, conversation)
            ai_msg = create_message(
                conversation,
                sender_type=SenderType.AI,
                message_text=ai_reply,
                metadata={"engine": "stub"},
            )
            ai_message_id = ai_msg.pk

        return InboundMessageResult(
            conversation_id=conversation.pk,
            session_key=conversation.session_key,
            contact_id=contact.pk,
            customer_message_id=customer_msg.pk,
            ai_message_id=ai_message_id,
            ai_reply=ai_reply,
            human_takeover=conversation.human_takeover,
            lead_id=lead_id,
            agent_run_id=agent_run_id,
            intent=intent,
        )

    @staticmethod
    def _run_agent(agent_instance, conversation, message_text):
        if agent_instance.template.slug not in InboundMessageService.IMPLEMENTED_SLUGS:
            return None
        return AgentOrchestrator.run(agent_instance, conversation, message_text)


class OutboundMessageService:
    """Send outbound messages to customers (channel-specific delivery in future)."""

    @staticmethod
    def send(conversation, message_text: str, sender_type: str = SenderType.AI) -> int:
        from apps.inbox.services import create_message

        msg = create_message(
            conversation,
            sender_type=sender_type,
            message_text=message_text,
        )
        return msg.pk
