"""Phase 7 tests: analytics module."""
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.models import User, UserRole
from apps.agent_engine.models import AgentRun
from apps.agents.models import AgentTemplate
from apps.agents.services import create_agent_instance
from apps.analytics.services import AnalyticsService
from apps.crm.models import Lead, LeadStatus
from apps.crm.services import create_contact, create_lead
from apps.inbox.models import ChannelType
from apps.integrations.services.message_pipeline import InboundMessageService
from apps.knowledge.services import create_knowledge_source
from apps.tenants.services import create_tenant


@pytest.fixture
def analytics_setup(client, db):
    tenant = create_tenant(name="Analytics Co")
    other_tenant = create_tenant(name="Other Co")
    User.objects.create_user(
        email="analytics@test.com",
        password="TestPass123!",
        full_name="Analytics Tester",
        tenant=tenant,
        role=UserRole.OWNER,
    )
    template = AgentTemplate.objects.create(
        name="Sales Closing Agent",
        slug="sales-closing-agent",
        description="Sales",
        category="Sales",
        is_implemented=True,
    )
    agent = create_agent_instance(tenant, template, status="active")
    other_agent = create_agent_instance(other_tenant, template, status="active", name="Other Agent")

    contact = create_contact(tenant, name="Lead One", email="lead@test.com", source="web_chat")
    create_lead(
        tenant,
        contact,
        title="Hot deal",
        agent_instance=agent,
        status=LeadStatus.HOT,
        source="web_chat",
        score=80,
    )
    create_lead(
        tenant,
        create_contact(tenant, name="Lead Two", source="instagram"),
        title="IG lead",
        agent_instance=agent,
        status=LeadStatus.NEW,
        source="instagram",
    )

    InboundMessageService.process(
        tenant,
        message_text="What is pricing?",
        channel_type=ChannelType.WEB_CHAT,
        customer_name="Web User",
        customer_email="web@test.com",
        agent_instance=agent,
        session_key="analytics-test-session",
    )

    create_knowledge_source(
        tenant,
        title="Pricing FAQ",
        content="Starter plan is $299 per month.",
        source_type="pricing",
        agent_instance=agent,
    )

    # Data for other tenant (must not leak)
    other_contact = create_contact(other_tenant, name="Other Lead", source="web_chat")
    create_lead(other_tenant, other_contact, title="Other lead", agent_instance=other_agent)
    AgentRun.objects.create(
        tenant=other_tenant,
        agent_instance=other_agent,
        input_message="other",
        output_message="other reply",
        intent="general",
    )

    client.login(username="analytics@test.com", password="TestPass123!")
    return client, tenant, agent, other_tenant


@pytest.mark.django_db
class TestAnalyticsOverviewAPI:
    def test_overview_api_works(self, analytics_setup):
        client, tenant, _, _ = analytics_setup
        response = client.get("/api/analytics/overview/?range=last_30_days")
        assert response.status_code == 200
        data = response.json()
        assert data["total_leads"] >= 2
        assert data["total_conversations"] >= 1
        assert data["total_agent_runs"] >= 1
        assert data["total_knowledge_sources"] >= 1

    def test_metrics_are_tenant_scoped(self, analytics_setup):
        client, tenant, _, other_tenant = analytics_setup
        response = client.get("/api/analytics/overview/?range=all_time")
        data = response.json()
        other_overview = AnalyticsService.get_overview_metrics(other_tenant, "all_time")
        # Two seeded leads plus one created by the inbound web chat pipeline
        assert data["total_leads"] == 3
        assert other_overview["total_leads"] == 1
        assert data["total_leads"] != other_overview["total_leads"]


@pytest.mark.django_db
class TestAnalyticsFunnel:
    def test_conversion_funnel_counts(self, analytics_setup):
        client, tenant, _, _ = analytics_setup
        response = client.get("/api/analytics/funnel/?range=all_time")
        assert response.status_code == 200
        data = response.json()
        assert data["total_leads"] == 3
        status_map = {s["status"]: s["count"] for s in data["stages"]}
        assert status_map["hot"] >= 1
        assert status_map["new"] >= 1

    def test_lead_source_breakdown(self, analytics_setup):
        client, tenant, _, _ = analytics_setup
        response = client.get("/api/analytics/overview/?range=all_time")
        sources = AnalyticsService.get_lead_source_breakdown(tenant, "all_time")
        source_map = {s["source"]: s["count"] for s in sources["sources"]}
        assert source_map["web_chat"] >= 1
        assert source_map["instagram"] == 1


@pytest.mark.django_db
class TestAnalyticsAgents:
    def test_agent_performance_includes_sales_agent(self, analytics_setup):
        client, tenant, agent, _ = analytics_setup
        response = client.get("/api/analytics/agents/?range=all_time")
        assert response.status_code == 200
        agents = response.json()["agents"]
        assert len(agents) >= 1
        sales = next(a for a in agents if a["agent_id"] == agent.pk)
        assert "Sales" in sales["template_name"] or sales["template_name"]
        assert sales["total_leads"] >= 3
        assert sales["knowledge_sources"] >= 1


@pytest.mark.django_db
class TestAnalyticsInbox:
    def test_inbox_analytics_counts(self, analytics_setup):
        client, tenant, _, _ = analytics_setup
        response = client.get("/api/analytics/inbox/?range=all_time")
        assert response.status_code == 200
        data = response.json()
        assert data["total_conversations"] >= 1
        assert data["total_messages"] >= 2
        assert data["customer_messages"] >= 1
        assert data["ai_messages"] >= 1


@pytest.mark.django_db
class TestAnalyticsAgentEngine:
    def test_agent_engine_counts_runs(self, analytics_setup):
        client, tenant, _, _ = analytics_setup
        response = client.get("/api/analytics/overview/?range=all_time")
        engine = AnalyticsService.get_agent_engine_metrics(tenant, "all_time")
        assert engine["total_runs"] >= 1
        assert engine["successful_runs"] >= 1
        assert "runs_by_intent" in engine
        assert len(engine["latest_runs"]) >= 1


@pytest.mark.django_db
class TestAnalyticsKnowledge:
    def test_knowledge_analytics_counts(self, analytics_setup):
        client, tenant, agent, _ = analytics_setup
        response = client.get("/api/analytics/knowledge/?range=all_time")
        assert response.status_code == 200
        data = response.json()
        assert data["total_knowledge_sources"] >= 1
        assert data["total_chunks"] >= 1
        assert len(data["top_agents_by_knowledge"]) >= 1


@pytest.mark.django_db
class TestAnalyticsDateFilter:
    def test_last_7_days_filter(self, analytics_setup):
        client, tenant, _, _ = analytics_setup
        old_contact = create_contact(tenant, name="Old Lead", source="manual")
        old_lead = create_lead(
            tenant,
            old_contact,
            title="Old lead",
            status=LeadStatus.LOST,
            source="manual",
        )
        Lead.objects.filter(pk=old_lead.pk).update(
            created_at=timezone.now() - timedelta(days=60)
        )

        all_time = AnalyticsService.get_overview_metrics(tenant, "all_time")
        last_7 = AnalyticsService.get_overview_metrics(tenant, "last_7_days")
        assert all_time["total_leads"] >= last_7["total_leads"]

    def test_all_time_includes_old_leads(self, analytics_setup):
        client, tenant, _, _ = analytics_setup
        response = client.get("/api/analytics/funnel/?range=all_time")
        assert response.status_code == 200


@pytest.mark.django_db
class TestAnalyticsUI:
    def test_dashboard_page_loads(self, analytics_setup):
        client, _, _, _ = analytics_setup
        response = client.get("/analytics/")
        assert response.status_code == 200
        assert b"Conversion Funnel" in response.content
        assert b"Agent Performance" in response.content

    def test_date_filter_on_page(self, analytics_setup):
        client, _, _, _ = analytics_setup
        response = client.get("/analytics/?range=last_7_days")
        assert response.status_code == 200
        assert b"Last 7 days" in response.content

    def test_empty_state_does_not_crash(self, client, db):
        tenant = create_tenant(name="Empty Analytics Co")
        User.objects.create_user(
            email="empty@test.com",
            password="TestPass123!",
            full_name="Empty User",
            tenant=tenant,
            role=UserRole.OWNER,
        )
        client.login(username="empty@test.com", password="TestPass123!")
        response = client.get("/analytics/")
        assert response.status_code == 200
        assert b"No leads in this period" in response.content or b"Total Leads" in response.content


@pytest.mark.django_db
class TestMainDashboardUsesAnalytics:
    def test_main_dashboard_uses_analytics_service(self, analytics_setup):
        client, tenant, _, _ = analytics_setup
        response = client.get("/dashboard/")
        assert response.status_code == 200
        overview = AnalyticsService.get_overview_metrics(tenant, "last_30_days")
        assert str(overview["total_leads"]).encode() in response.content
        assert str(overview["hot_leads"]).encode() in response.content
