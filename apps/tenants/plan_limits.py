"""Soft plan limit checks for tenant operations."""
from dataclasses import dataclass

from apps.tenants.models import Tenant
from apps.tenants.usage import get_tenant_plan, get_tenant_usage


@dataclass
class LimitCheckResult:
    allowed: bool
    at_limit: bool
    message: str
    current: int
    max_limit: int | None


def _check(current: int, max_limit: int | None, resource: str) -> LimitCheckResult:
    if max_limit is None:
        return LimitCheckResult(
            allowed=True,
            at_limit=False,
            message="",
            current=current,
            max_limit=None,
        )
    at_limit = current >= max_limit
    if at_limit:
        upgrade_hint = "Upgrade your plan in Settings -> Plans."
        resource_messages = {
            "active agents": (
                f"Agent deployment limit reached ({current}/{max_limit}). "
                f"Deactivate an agent or {upgrade_hint.lower()}"
            ),
            "knowledge sources": (
                f"Knowledge source limit reached ({current}/{max_limit}). "
                f"Remove a source or {upgrade_hint.lower()}"
            ),
            "integration channels": (
                f"Integration channel limit reached ({current}/{max_limit}). "
                f"Remove a channel or {upgrade_hint.lower()}"
            ),
            "messages this month": (
                f"Monthly message limit reached ({current}/{max_limit}). "
                f"{upgrade_hint}"
            ),
        }
        message = resource_messages.get(
            resource,
            (
                f"Your plan allows up to {max_limit} {resource}. "
                f"You currently have {current}. {upgrade_hint}"
            ),
        )
        return LimitCheckResult(
            allowed=False,
            at_limit=True,
            message=message,
            current=current,
            max_limit=max_limit,
        )
    return LimitCheckResult(
        allowed=True,
        at_limit=False,
        message="",
        current=current,
        max_limit=max_limit,
    )


def check_agent_limit(tenant: Tenant) -> LimitCheckResult:
    plan = get_tenant_plan(tenant)
    usage = get_tenant_usage(tenant)
    return _check(
        usage.active_agents,
        plan.max_agents if plan else None,
        "active agents",
    )


def check_team_member_limit(tenant: Tenant) -> LimitCheckResult:
    plan = get_tenant_plan(tenant)
    usage = get_tenant_usage(tenant)
    return _check(
        usage.team_members,
        plan.max_team_members if plan else None,
        "team members",
    )


def check_knowledge_limit(tenant: Tenant) -> LimitCheckResult:
    plan = get_tenant_plan(tenant)
    usage = get_tenant_usage(tenant)
    return _check(
        usage.knowledge_sources,
        plan.max_knowledge_sources if plan else None,
        "knowledge sources",
    )


def check_integration_limit(tenant: Tenant) -> LimitCheckResult:
    plan = get_tenant_plan(tenant)
    usage = get_tenant_usage(tenant)
    return _check(
        usage.integrations_connected,
        plan.max_integrations if plan else None,
        "integration channels",
    )


def check_message_limit(tenant: Tenant) -> LimitCheckResult:
    plan = get_tenant_plan(tenant)
    usage = get_tenant_usage(tenant)
    return _check(
        usage.messages_this_month,
        plan.max_monthly_messages if plan else None,
        "messages this month",
    )
