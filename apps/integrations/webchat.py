"""Web chat integration handler."""
from apps.agents.models import AgentInstance
from apps.integrations.services.message_pipeline import InboundMessageService
from apps.tenants.models import Tenant


def handle_webchat_message(
    tenant: Tenant,
    *,
    message_text: str,
    customer_name: str = "Web Chat Visitor",
    customer_email: str = "",
    customer_phone: str = "",
    agent_instance_id: int | None = None,
    session_key: str = "",
) -> dict:
    agent_instance = None
    if agent_instance_id:
        agent_instance = AgentInstance.objects.filter(
            tenant=tenant, pk=agent_instance_id, status="active"
        ).select_related("template").prefetch_related("settings").first()
    if not agent_instance:
        agent_instance = (
            AgentInstance.objects.filter(tenant=tenant, status="active")
            .select_related("template")
            .prefetch_related("settings")
            .first()
        )

    result = InboundMessageService.process(
        tenant,
        message_text=message_text,
        customer_name=customer_name,
        customer_email=customer_email,
        customer_phone=customer_phone,
        agent_instance=agent_instance,
        session_key=session_key,
    )

    return {
        "conversation_id": result.conversation_id,
        "session_key": result.session_key,
        "contact_id": result.contact_id,
        "customer_message_id": result.customer_message_id,
        "ai_message_id": result.ai_message_id,
        "ai_reply": result.ai_reply,
        "human_takeover": result.human_takeover,
        "lead_id": result.lead_id,
        "agent_run_id": result.agent_run_id,
        "intent": result.intent,
    }
