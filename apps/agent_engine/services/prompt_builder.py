"""Build structured prompts for agent runs."""
from apps.agents.models import AgentInstance
from apps.inbox.models import Conversation


class PromptBuilder:
    """Assemble system and user prompts from agent config and context."""

    SAFETY_RULES = [
        "Do not promise guaranteed results.",
        "Do not invent pricing if not present in knowledge or pricing settings.",
        "Do not give legal, medical, or financial advice.",
        "Do not claim to be human.",
        "Always ask a clarifying question if information is missing.",
        "Always hand off to human for sensitive or final commercial decisions.",
    ]

    @classmethod
    def build_system_prompt(
        cls,
        agent_instance: AgentInstance,
        knowledge_context: str = "",
    ) -> str:
        settings = getattr(agent_instance, "settings", None)
        business_name = settings.business_name if settings else agent_instance.name
        business_desc = settings.business_description if settings else ""
        services = settings.services_json if settings else []
        pricing = settings.pricing_json if settings else {}
        tone = agent_instance.tone
        language = agent_instance.language

        services_text = ", ".join(services) if isinstance(services, list) else str(services)
        pricing_text = cls._format_pricing(pricing)

        lines = [
            f"You are a professional AI sales assistant for {business_name}.",
            f"Business: {business_name}",
            f"Tone: {tone}. Language: {language}.",
        ]
        if business_desc:
            lines.append(f"Description: {business_desc}")
        if services_text:
            lines.append(f"Services: {services_text}")
        if pricing_text:
            lines.append(f"Pricing: {pricing_text}")
        if knowledge_context:
            lines.append(f"Knowledge base:\n{knowledge_context}")
        lines.append("Safety rules:")
        lines.extend(f"- {rule}" for rule in cls.SAFETY_RULES)
        if settings and settings.qualification_questions_json:
            lines.append("Qualification questions to ask when appropriate:")
            for q in settings.qualification_questions_json:
                lines.append(f"- {q}")
        return "\n".join(lines)

    @classmethod
    def build_user_prompt(
        cls,
        customer_message: str,
        conversation: Conversation,
        recent_messages: list[str] | None = None,
    ) -> str:
        parts = []
        if recent_messages:
            parts.append("Recent conversation:")
            parts.extend(recent_messages[-6:])
        parts.append(f"Customer message: {customer_message}")
        contact = conversation.contact
        if contact.name:
            parts.append(f"Customer name: {contact.name}")
        return "\n".join(parts)

    @staticmethod
    def _format_pricing(pricing: dict | list) -> str:
        if isinstance(pricing, dict) and pricing:
            return "; ".join(f"{k}: {v}" for k, v in pricing.items())
        if isinstance(pricing, list):
            return "; ".join(str(p) for p in pricing)
        return ""
