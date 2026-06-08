"""Phase 12 tests: agent scenario library and playground."""
import pytest

from apps.accounts.models import User, UserRole
from apps.agent_engine.demo_scenarios import SCENARIOS, get_scenarios_for_slug
from apps.agent_engine.models import AgentRun
from apps.agent_engine.services.scenario_runner import run_scenario
from apps.agents.models import AgentTemplate
from apps.agents.services import create_agent_instance, update_agent_settings
from apps.inbox.models import ChannelType, Conversation
from apps.integrations.models import ChannelCredential
from apps.inbox.models import ChannelAccount
from apps.integrations.services.channel_service import simulate_test_message
from apps.tenants.services import create_tenant


@pytest.fixture
def scenario_setup(client, db):
    tenant = create_tenant(name="Scenario Co")
    User.objects.create_user(
        email="scenario@test.com",
        password="TestPass123!",
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
    update_agent_settings(agent, business_name="Scenario Co")
    client.login(username="scenario@test.com", password="TestPass123!")
    return client, tenant, agent


@pytest.mark.django_db
class TestScenarioLibrary:
    def test_total_scenarios_at_least_fifty(self):
        assert len(SCENARIOS) >= 50

    def test_sales_has_five_scenarios(self):
        assert len(get_scenarios_for_slug("sales-closing-agent")) >= 5


@pytest.mark.django_db
class TestPlaygroundScenarios:
    def test_playground_loads_scenarios(self, scenario_setup):
        client, _, agent = scenario_setup
        response = client.get(f"/agents/instances/{agent.pk}/playground/")
        assert response.status_code == 200
        assert b"Demo scenario" in response.content or b"scenario" in response.content.lower()

    def test_running_scenario_returns_reply_and_agent_run(self, scenario_setup):
        client, tenant, agent = scenario_setup
        scenario = get_scenarios_for_slug("sales-closing-agent")[0]
        response = client.post(
            f"/agents/instances/{agent.pk}/playground/",
            {
                "channel": "web_chat",
                "scenario_id": scenario.id,
                "message_text": scenario.customer_message,
                "action": "send",
            },
        )
        assert response.status_code == 200
        assert AgentRun.objects.filter(tenant=tenant, agent_instance=agent).exists()

    def test_scenario_intent_comparison_shown(self, scenario_setup):
        client, _, agent = scenario_setup
        scenario = get_scenarios_for_slug("sales-closing-agent")[1]
        response = client.post(
            f"/agents/instances/{agent.pk}/playground/",
            {
                "channel": "web_chat",
                "scenario_id": scenario.id,
                "message_text": scenario.customer_message,
                "action": "send",
            },
        )
        assert response.status_code == 200
        assert b"intent_matched" in response.content or b"Quality checks" in response.content

    def test_whatsapp_mock_from_channel_test(self, scenario_setup):
        _, tenant, agent = scenario_setup
        account = ChannelAccount.objects.create(
            tenant=tenant,
            channel_type=ChannelType.WHATSAPP,
            display_name="WA Scenario Test",
            mock_mode=True,
        )
        ChannelCredential.objects.create(
            tenant=tenant,
            channel_account=account,
            phone_number_id="scenario_wa_phone",
        )
        result = simulate_test_message(
            tenant,
            account,
            message_text="Hello, what is pricing?",
            customer_name="WA Scenario User",
            customer_phone="+15550009999",
            agent_instance=agent,
        )
        assert result["success"] is True
        assert Conversation.objects.filter(tenant=tenant, channel_type=ChannelType.WHATSAPP).exists()

    def test_instagram_mock_from_playground(self, scenario_setup):
        client, tenant, agent = scenario_setup
        scenario = get_scenarios_for_slug("sales-closing-agent")[0]
        response = client.post(
            f"/agents/instances/{agent.pk}/playground/",
            {
                "channel": "instagram_mock",
                "scenario_id": scenario.id,
                "message_text": scenario.customer_message,
                "action": "send",
            },
        )
        assert response.status_code == 200
        assert Conversation.objects.filter(tenant=tenant, channel_type=ChannelType.INSTAGRAM).exists()


@pytest.mark.django_db
class TestSafetyHandoffScenarios:
    def test_clinic_urgent_handoff(self, db):
        tenant = create_tenant(name="Safety Clinic")
        template = AgentTemplate.objects.create(
            slug="clinic-agent", name="Clinic", description="C", category="C", is_implemented=True
        )
        agent = create_agent_instance(tenant, template, status="active")
        scenario = next(s for s in SCENARIOS if s.id == "clinic-urgent")
        result = run_scenario(agent, scenario)
        assert result.should_handoff is True

    def test_finance_tax_handoff(self, db):
        tenant = create_tenant(name="Safety Finance")
        template = AgentTemplate.objects.create(
            slug="finance-agent", name="Finance", description="F", category="F", is_implemented=True
        )
        agent = create_agent_instance(tenant, template, status="active")
        scenario = next(s for s in SCENARIOS if s.id == "fin-tax")
        result = run_scenario(agent, scenario)
        assert result.should_handoff is True

    def test_ecommerce_refund_handoff(self, db):
        tenant = create_tenant(name="Safety Ecom")
        template = AgentTemplate.objects.create(
            slug="ecommerce-agent", name="Ecom", description="E", category="E", is_implemented=True
        )
        agent = create_agent_instance(tenant, template, status="active")
        scenario = next(s for s in SCENARIOS if s.id == "eco-refund")
        result = run_scenario(agent, scenario)
        assert result.should_handoff is True

    def test_real_estate_legal_handoff(self, db):
        tenant = create_tenant(name="Safety RE")
        template = AgentTemplate.objects.create(
            slug="real-estate-agent", name="RE", description="R", category="R", is_implemented=True
        )
        agent = create_agent_instance(tenant, template, status="active")
        scenario = next(s for s in SCENARIOS if s.id == "re-legal-handoff")
        result = run_scenario(agent, scenario)
        assert result.should_handoff is True

    def test_tender_pricing_handoff(self, db):
        tenant = create_tenant(name="Safety Tender")
        template = AgentTemplate.objects.create(
            slug="tender-agent", name="Tender", description="T", category="T", is_implemented=True
        )
        agent = create_agent_instance(tenant, template, status="active")
        scenario = next(s for s in SCENARIOS if s.id == "tender-pricing")
        result = run_scenario(agent, scenario)
        assert result.should_handoff is True
