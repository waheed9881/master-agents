"""Agent instance creation and configuration services."""
from apps.agents.models import (
    AgentInstance,
    AgentInstanceStatus,
    AgentSettings,
    AgentTemplate,
)
from apps.tenants.models import Tenant

DEFAULT_QUALIFICATION_QUESTIONS = [
    "What service are you looking for?",
    "What type of business do you have?",
    "What is your budget range?",
    "What is your timeline?",
    "Would you like to schedule a call/demo/visit?",
]

DEFAULT_HANDOFF_RULES = {
    "triggers": [
        "customer_ready_to_pay",
        "custom_quote_request",
        "angry_customer",
        "discount_request",
        "legal_medical_financial_guarantee",
        "low_ai_confidence",
        "speak_with_human",
    ],
    "auto_notify_sales": True,
}


def create_agent_instance(
    tenant: Tenant,
    template: AgentTemplate,
    *,
    name: str | None = None,
    status: str = AgentInstanceStatus.DRAFT,
    language: str = "en",
    tone: str = "professional",
) -> AgentInstance:
    """Create an agent instance with default settings for the tenant."""
    instance = AgentInstance.objects.create(
        tenant=tenant,
        template=template,
        name=name or template.name,
        status=status,
        language=language,
        tone=tone,
    )
    AgentSettings.objects.create(
        agent_instance=instance,
        qualification_questions_json=DEFAULT_QUALIFICATION_QUESTIONS,
        handoff_rules_json=DEFAULT_HANDOFF_RULES,
        working_hours_json={"timezone": tenant.timezone, "days": "Mon-Fri 9-18"},
    )
    return instance


def activate_agent_instance(instance: AgentInstance) -> AgentInstance:
    instance.status = AgentInstanceStatus.ACTIVE
    instance.save(update_fields=["status", "updated_at"])
    return instance


def update_agent_settings(instance: AgentInstance, **fields) -> AgentSettings:
    settings, _ = AgentSettings.objects.get_or_create(agent_instance=instance)
    for key, value in fields.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    settings.save()
    return settings
