"""Tenant usage metrics for plan limits and dashboards."""
from dataclasses import dataclass
from datetime import datetime

from django.db.models import Sum
from django.utils import timezone

from apps.agent_engine.models import AgentRun
from apps.agents.models import AgentInstance, AgentInstanceStatus
from apps.inbox.models import ChannelAccount, Message
from apps.knowledge.models import KnowledgeSource
from apps.tenants.models import Plan, Tenant, TenantSubscription


@dataclass
class TenantUsage:
    active_agents: int
    team_members: int
    messages_this_month: int
    knowledge_sources: int
    integrations_connected: int
    agent_runs_this_month: int
    tokens_used_this_month: int
    estimated_ai_cost_this_month: float


def _month_start() -> datetime:
    now = timezone.now()
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def get_tenant_usage(tenant: Tenant) -> TenantUsage:
    """Compute current usage counters for a tenant."""
    month_start = _month_start()
    runs_qs = AgentRun.objects.filter(tenant=tenant, created_at__gte=month_start)
    agg = runs_qs.aggregate(
        total_tokens=Sum("tokens_used"),
        total_cost=Sum("cost_estimate"),
    )
    return TenantUsage(
        active_agents=AgentInstance.objects.filter(
            tenant=tenant,
            status=AgentInstanceStatus.ACTIVE,
        ).count(),
        team_members=tenant.users.filter(is_active=True).count(),
        messages_this_month=Message.objects.filter(
            conversation__tenant=tenant,
            created_at__gte=month_start,
        ).count(),
        knowledge_sources=KnowledgeSource.objects.filter(tenant=tenant).count(),
        integrations_connected=ChannelAccount.objects.filter(
            tenant=tenant,
            is_active=True,
        ).count(),
        agent_runs_this_month=runs_qs.count(),
        tokens_used_this_month=int(agg["total_tokens"] or 0),
        estimated_ai_cost_this_month=float(agg["total_cost"] or 0),
    )


def get_tenant_plan(tenant: Tenant) -> Plan | None:
    sub = TenantSubscription.objects.filter(tenant=tenant).select_related("plan").first()
    return sub.plan if sub else None


def usage_with_limits(tenant: Tenant) -> dict:
    """Return usage metrics alongside plan limits for UI progress bars."""
    usage = get_tenant_usage(tenant)
    plan = get_tenant_plan(tenant)
    limits = {
        "max_agents": plan.max_agents if plan else None,
        "max_team_members": plan.max_team_members if plan else None,
        "max_monthly_messages": plan.max_monthly_messages if plan else None,
        "max_knowledge_sources": plan.max_knowledge_sources if plan else None,
        "max_integrations": plan.max_integrations if plan else None,
    }
    return {
        "usage": usage,
        "plan": plan,
        "limits": limits,
        "subscription": getattr(tenant, "subscription", None),
    }
