"""Read-optimized query helpers for agents."""
from django.db.models import QuerySet

from apps.agents.models import AgentInstance, AgentTemplate
from apps.tenants.models import Tenant


def list_active_templates() -> QuerySet[AgentTemplate]:
    return AgentTemplate.objects.filter(is_active=True)


def get_template_by_slug(slug: str) -> AgentTemplate | None:
    return AgentTemplate.objects.filter(slug=slug, is_active=True).first()


def get_template_by_id(template_id: int) -> AgentTemplate | None:
    return AgentTemplate.objects.filter(pk=template_id, is_active=True).first()


def list_tenant_agents(tenant: Tenant) -> QuerySet[AgentInstance]:
    return (
        AgentInstance.objects.filter(tenant=tenant)
        .select_related("template")
        .prefetch_related("settings")
    )


def get_tenant_agent(tenant: Tenant, agent_id: int) -> AgentInstance | None:
    return (
        AgentInstance.objects.filter(tenant=tenant, pk=agent_id)
        .select_related("template")
        .prefetch_related("settings")
        .first()
    )


def tenant_has_agent_for_template(tenant: Tenant, template: AgentTemplate) -> bool:
    return AgentInstance.objects.filter(tenant=tenant, template=template).exists()
