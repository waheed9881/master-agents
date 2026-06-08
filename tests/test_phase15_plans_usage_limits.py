"""Phase 15 tests: plans, usage, and limit enforcement."""
import pytest

from apps.accounts.models import User, UserRole
from apps.agents.models import AgentInstanceStatus, AgentTemplate
from apps.agents.services import create_agent_instance
from apps.inbox.models import ChannelAccount, ChannelType
from apps.knowledge.models import KnowledgeSource
from apps.tenants.plan_limits import (
    check_agent_limit,
    check_integration_limit,
    check_knowledge_limit,
)
from apps.tenants.plan_services import ensure_tenant_subscription, seed_plans
from apps.tenants.services import create_tenant
from apps.tenants.usage import get_tenant_usage


@pytest.fixture
def plan_setup(client, db):
    seed_plans()
    tenant = create_tenant(name="Plan Co")
    ensure_tenant_subscription(tenant, plan_slug="starter")
    user = User.objects.create_user(
        email="plan@limits.test",
        password="TestPass123!",
        tenant=tenant,
        role=UserRole.OWNER,
    )
    template = AgentTemplate.objects.create(
        slug="sales-closing-agent",
        name="Sales",
        description="S",
        category="S",
        is_implemented=True,
    )
    client.login(username=user.email, password="TestPass123!")
    return client, tenant, template


@pytest.mark.django_db
class TestPlansAndLimits:
    def test_plans_are_seeded(self, db):
        plans = seed_plans()
        assert len(plans) == 4
        slugs = {p.slug for p in plans}
        assert slugs == {"starter", "growth", "pro", "enterprise"}

    def test_tenant_has_subscription_after_seed(self, plan_setup):
        _, tenant, _ = plan_setup
        tenant.refresh_from_db()
        assert tenant.subscription.plan.slug == "starter"

    def test_plan_usage_page_shows_usage(self, plan_setup):
        client, _, _ = plan_setup
        response = client.get("/settings/plan/")
        assert response.status_code == 200
        assert b"Plans" in response.content or b"plan" in response.content.lower()

    def test_agent_deployment_respects_max_agents(self, plan_setup):
        client, tenant, template = plan_setup
        create_agent_instance(tenant, template, status=AgentInstanceStatus.ACTIVE)
        AgentTemplate.objects.create(
            slug="clinic-agent",
            name="Clinic",
            description="C",
            category="C",
            is_implemented=True,
        )
        limit = check_agent_limit(tenant)
        assert limit.at_limit is True
        assert limit.allowed is False

        before = tenant.agent_instances.filter(status=AgentInstanceStatus.ACTIVE).count()
        response = client.post("/agents/templates/clinic-agent/deploy/")
        assert response.status_code == 302
        after = tenant.agent_instances.filter(status=AgentInstanceStatus.ACTIVE).count()
        assert after == before

    def test_knowledge_limit_enforced(self, plan_setup):
        _, tenant, _ = plan_setup
        plan = tenant.subscription.plan
        for i in range(plan.max_knowledge_sources):
            KnowledgeSource.objects.create(
                tenant=tenant,
                title=f"Source {i}",
                content="content",
            )
        limit = check_knowledge_limit(tenant)
        assert limit.allowed is False

    def test_integration_limit_enforced(self, plan_setup):
        _, tenant, _ = plan_setup
        plan = tenant.subscription.plan
        for i in range(plan.max_integrations):
            ChannelAccount.objects.create(
                tenant=tenant,
                channel_type=ChannelType.WEB_CHAT,
                display_name=f"Channel {i}",
            )
        limit = check_integration_limit(tenant)
        assert limit.allowed is False

    def test_usage_metrics(self, plan_setup):
        _, tenant, _ = plan_setup
        usage = get_tenant_usage(tenant)
        assert usage.team_members >= 1
