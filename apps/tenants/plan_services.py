"""Plan seeding and subscription management."""
from datetime import timedelta

from django.utils import timezone

from apps.tenants.models import Plan, SubscriptionStatus, Tenant, TenantSubscription

DEFAULT_PLANS = [
    {
        "name": "Starter",
        "slug": "starter",
        "monthly_price": 299,
        "max_agents": 1,
        "max_team_members": 3,
        "max_monthly_messages": 1000,
        "max_knowledge_sources": 10,
        "max_integrations": 1,
        "allow_real_ai_provider": False,
        "allow_whatsapp": False,
        "allow_instagram": False,
    },
    {
        "name": "Growth",
        "slug": "growth",
        "monthly_price": 599,
        "max_agents": 3,
        "max_team_members": 10,
        "max_monthly_messages": 5000,
        "max_knowledge_sources": 50,
        "max_integrations": 3,
        "allow_real_ai_provider": True,
        "allow_whatsapp": True,
        "allow_instagram": False,
    },
    {
        "name": "Pro",
        "slug": "pro",
        "monthly_price": 999,
        "max_agents": 10,
        "max_team_members": 25,
        "max_monthly_messages": 25000,
        "max_knowledge_sources": 200,
        "max_integrations": 10,
        "allow_real_ai_provider": True,
        "allow_whatsapp": True,
        "allow_instagram": True,
    },
    {
        "name": "Enterprise",
        "slug": "enterprise",
        "monthly_price": 0,
        "max_agents": 999,
        "max_team_members": 999,
        "max_monthly_messages": 999999,
        "max_knowledge_sources": 9999,
        "max_integrations": 999,
        "allow_real_ai_provider": True,
        "allow_whatsapp": True,
        "allow_instagram": True,
    },
]


def seed_plans() -> list[Plan]:
    """Create or update default SaaS plans."""
    plans = []
    for data in DEFAULT_PLANS:
        plan, _ = Plan.objects.update_or_create(
            slug=data["slug"],
            defaults=data,
        )
        plans.append(plan)
    return plans


def ensure_tenant_subscription(
    tenant: Tenant,
    plan_slug: str = "enterprise",
) -> TenantSubscription:
    """Assign a plan to a tenant if none exists."""
    existing = TenantSubscription.objects.filter(tenant=tenant).first()
    if existing:
        return existing
    plan = Plan.objects.filter(slug=plan_slug, is_active=True).first()
    if not plan:
        seed_plans()
        plan = Plan.objects.get(slug=plan_slug)
    now = timezone.now()
    return TenantSubscription.objects.create(
        tenant=tenant,
        plan=plan,
        status=SubscriptionStatus.ACTIVE,
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
    )


def change_tenant_plan(tenant: Tenant, plan: Plan) -> TenantSubscription:
    """Switch tenant to a different plan (local demo only)."""
    now = timezone.now()
    sub, _ = TenantSubscription.objects.update_or_create(
        tenant=tenant,
        defaults={
            "plan": plan,
            "status": SubscriptionStatus.ACTIVE,
            "current_period_start": now,
            "current_period_end": now + timedelta(days=30),
        },
    )
    return sub
