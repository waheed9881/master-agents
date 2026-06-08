"""Phase 5 tests: agent engine and SalesClosingAgent."""
import pytest

from apps.accounts.models import User, UserRole
from apps.agent_engine.models import AgentRun
from apps.agent_engine.providers.mock import MockAIProvider
from apps.agent_engine.services.handoff_decision import HandoffDecisionService
from apps.agent_engine.services.lead_extraction import LeadExtractionService
from apps.agent_engine.services.orchestrator import AgentOrchestrator
from apps.agent_modules.sales_agent.agent import SalesClosingAgent
from apps.agents.models import AgentTemplate
from apps.agents.services import create_agent_instance, update_agent_settings
from apps.crm.models import Lead, LeadStatus
from apps.crm.services import detect_hot_lead
from apps.inbox.services import find_or_create_contact, find_or_create_conversation
from apps.tenants.services import create_tenant


@pytest.fixture
def sales_agent_setup(client, db):
    tenant = create_tenant(name="Agent Engine Co")
    User.objects.create_user(
        email="agentengine@test.com",
        password="TestPass123!",
        full_name="Engine Tester",
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
    update_agent_settings(
        agent,
        business_name="Test Corp",
        pricing_json={"Starter": "$299/month"},
        services_json=["WhatsApp automation"],
    )
    client.login(username="agentengine@test.com", password="TestPass123!")
    return client, tenant, agent


@pytest.mark.django_db
class TestMockAIProvider:
    def test_pricing_intent(self):
        provider = MockAIProvider()
        result = provider.complete(
            "Business: Test Corp\nPricing: Starter: $299/month",
            "Customer message: How much does it cost?",
        )
        assert result.intent == "pricing_inquiry"
        assert "budget" in result.text.lower() or "pricing" in result.text.lower()

    def test_demo_intent(self):
        provider = MockAIProvider()
        result = provider.complete(
            "Business: Test Corp",
            "Customer message: Can I schedule a demo?",
        )
        assert result.intent == "demo_request"


@pytest.mark.django_db
class TestLeadExtraction:
    def test_extract_email_and_budget(self):
        data = LeadExtractionService.extract(
            "My email is buyer@test.com and budget is $500-1000/month"
        )
        assert data.email == "buyer@test.com"
        assert data.budget
        assert "budget_shared" in data.raw_signals


@pytest.mark.django_db
class TestHandoffDecision:
    def test_angry_customer_handoff(self):
        decision = HandoffDecisionService.evaluate("I am very angry and want a refund")
        assert decision.should_handoff is True

    def test_normal_message_no_handoff(self):
        decision = HandoffDecisionService.evaluate(
            "Hello, what services do you offer?",
            intent="greeting",
            confidence=0.9,
        )
        assert decision.should_handoff is False


@pytest.mark.django_db
class TestSalesClosingAgent:
    def test_agent_run_creates_lead(self, sales_agent_setup):
        _, tenant, agent = sales_agent_setup
        contact = find_or_create_contact(tenant, name="Buyer Test", email="buyer@test.com")
        conversation = find_or_create_conversation(tenant, contact, agent_instance=agent)

        sales_agent = SalesClosingAgent(agent, provider=MockAIProvider())
        result = sales_agent.run(
            "Hi, I need WhatsApp automation. Budget is $500/month. Need it in 2 weeks.",
            conversation,
        )

        assert result.reply
        assert result.lead_id
        lead = Lead.objects.get(pk=result.lead_id)
        assert lead.contact == contact
        assert lead.agent_instance == agent

    def test_hot_lead_detection(self, sales_agent_setup):
        _, tenant, agent = sales_agent_setup
        contact = find_or_create_contact(tenant, name="Hot Lead", email="hot@test.com")
        conversation = find_or_create_conversation(tenant, contact, agent_instance=agent)

        sales_agent = SalesClosingAgent(agent, provider=MockAIProvider())
        result = sales_agent.run(
            "I want to buy now. Budget $2000/month. Call me at +1234567890",
            conversation,
        )

        lead = Lead.objects.get(pk=result.lead_id)
        assert lead.status in (LeadStatus.HOT, LeadStatus.QUALIFYING, LeadStatus.QUALIFIED, LeadStatus.DEMO_BOOKED)
        assert lead.score > 0

    def test_handoff_on_human_request(self, sales_agent_setup):
        _, tenant, agent = sales_agent_setup
        contact = find_or_create_contact(tenant, name="Handoff Test")
        conversation = find_or_create_conversation(tenant, contact, agent_instance=agent)

        sales_agent = SalesClosingAgent(agent, provider=MockAIProvider())
        result = sales_agent.run_with_handoff("I want to speak with a human please", conversation)

        assert result.should_handoff is True
        conversation.refresh_from_db()
        assert conversation.human_takeover is True


@pytest.mark.django_db
class TestWebChatWithAgentEngine:
    def test_webchat_creates_agent_run(self, sales_agent_setup):
        client, _, agent = sales_agent_setup
        response = client.post(
            "/api/webchat/message/",
            {
                "message_text": "Hello, I need pricing for WhatsApp automation",
                "customer_name": "Web Buyer",
                "customer_email": "webbuyer@test.com",
                "agent_instance_id": agent.pk,
            },
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["ai_reply"]
        assert data["lead_id"]
        assert data["agent_run_id"]
        assert AgentRun.objects.filter(pk=data["agent_run_id"]).exists()

    def test_test_message_api(self, sales_agent_setup):
        client, _, agent = sales_agent_setup
        response = client.post(
            "/api/agent-engine/test-message/",
            {
                "message_text": "Schedule a demo please",
                "agent_instance_id": agent.pk,
                "customer_name": "API Tester",
            },
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["intent"] == "demo_request"

    def test_lead_score_updates_after_message(self, sales_agent_setup):
        client, tenant, agent = sales_agent_setup
        client.post(
            "/api/webchat/message/",
            {
                "message_text": "Budget $1000/month, need demo ASAP, email me at score@test.com",
                "agent_instance_id": agent.pk,
            },
            content_type="application/json",
        )
        lead = Lead.objects.filter(tenant=tenant).latest("created_at")
        assert lead.score > 0

    def test_orchestrator_resolves_sales_agent(self, sales_agent_setup):
        _, tenant, agent = sales_agent_setup
        contact = find_or_create_contact(tenant, name="Orch Test")
        conversation = find_or_create_conversation(tenant, contact, agent_instance=agent)
        result = AgentOrchestrator.run(agent, conversation, "Hello there")
        assert result is not None
        assert result.agent_result.reply
