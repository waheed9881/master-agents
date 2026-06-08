"""Phase 11 tests: all 10 agent brain modules."""
import pytest

from apps.agent_engine.models import AgentRun
from apps.agent_engine.providers.mock import MockAIProvider
from apps.agent_engine.services.orchestrator import AgentOrchestrator
from apps.agent_modules.registry import AGENT_CLASS_NAMES, is_agent_implemented, load_agent_class
from apps.agents.models import AgentTemplate
from apps.agents.services import create_agent_instance, update_agent_settings
from apps.crm.models import Lead
from apps.inbox.services import find_or_create_contact, find_or_create_conversation
from apps.tenants.services import create_tenant

ALL_SLUGS = list(AGENT_CLASS_NAMES.keys())

AGENT_TEST_MESSAGES = {
    "sales-closing-agent": "Hello, I need pricing for WhatsApp automation. Budget $500/month.",
    "real-estate-agent": "I want a 3 bedroom apartment downtown. Budget $300k. Can I schedule a visit?",
    "clinic-agent": "I need to book an appointment with the dentist next week.",
    "home-services-agent": "I have a plumbing leak, urgent! My address is 123 Main St.",
    "school-agent": "I want to enroll my child in grade 5. What are the fees?",
    "voice-agent": "Please call me back about my billing question.",
    "tender-agent": "We have an RFP due next month. Can you help with a proposal?",
    "ecommerce-agent": "Where is my order #ORD12345? It has not arrived.",
    "recruitment-agent": "I want to apply for the developer role. Here is my CV.",
    "finance-agent": "I have a question about invoice INV-2024-001 payment.",
}


@pytest.fixture
def brain_tenant(db):
    return create_tenant(name="Brain Test Co")


def _ensure_template(slug: str) -> AgentTemplate:
    names = {
        "sales-closing-agent": "Sales Closing Agent",
        "real-estate-agent": "Real Estate Agent",
        "clinic-agent": "Clinic Agent",
        "home-services-agent": "Home Services Agent",
        "school-agent": "School Agent",
        "voice-agent": "Voice Agent",
        "tender-agent": "Tender Agent",
        "ecommerce-agent": "eCommerce Agent",
        "recruitment-agent": "Recruitment Agent",
        "finance-agent": "Finance Agent",
    }
    template, _ = AgentTemplate.objects.get_or_create(
        slug=slug,
        defaults={
            "name": names.get(slug, slug),
            "description": "Test",
            "category": "Test",
            "is_implemented": True,
        },
    )
    template.is_implemented = True
    template.save(update_fields=["is_implemented"])
    return template


@pytest.mark.django_db
class TestAgentRegistry:
    def test_all_10_templates_implemented(self):
        for slug in ALL_SLUGS:
            assert is_agent_implemented(slug), f"{slug} not implemented"

    @pytest.mark.parametrize("slug", ALL_SLUGS)
    def test_orchestrator_loads_agent_class(self, brain_tenant, slug):
        template = _ensure_template(slug)
        agent = create_agent_instance(brain_tenant, template, status="active")
        update_agent_settings(agent, business_name="Brain Test Co")
        resolved = AgentOrchestrator.resolve_agent(agent)
        assert resolved is not None
        assert resolved.template_slug == slug

    @pytest.mark.parametrize("slug", ALL_SLUGS)
    def test_agent_returns_reply_with_mock_provider(self, brain_tenant, slug):
        template = _ensure_template(slug)
        instance = create_agent_instance(brain_tenant, template, status="active")
        update_agent_settings(instance, business_name="Brain Test Co")
        contact = find_or_create_contact(brain_tenant, name=f"Tester {slug}")
        conversation = find_or_create_conversation(brain_tenant, contact, agent_instance=instance)

        agent_cls = load_agent_class(slug)
        agent = agent_cls(instance, provider=MockAIProvider())
        message = AGENT_TEST_MESSAGES.get(slug, "Hello, I need help")
        result = agent.run(message, conversation)

        assert result.reply
        assert result.intent

    @pytest.mark.parametrize("slug", ALL_SLUGS)
    def test_agent_creates_agent_run_via_orchestrator(self, brain_tenant, slug):
        template = _ensure_template(slug)
        instance = create_agent_instance(brain_tenant, template, status="active")
        update_agent_settings(instance, business_name="Brain Test Co")
        contact = find_or_create_contact(brain_tenant, name=f"Orch {slug}")
        conversation = find_or_create_conversation(brain_tenant, contact, agent_instance=instance)

        message = AGENT_TEST_MESSAGES.get(slug, "Hello")
        orchestrated = AgentOrchestrator.run(instance, conversation, message)
        assert orchestrated is not None
        assert AgentRun.objects.filter(pk=orchestrated.agent_run_id).exists()

    @pytest.mark.parametrize("slug", ALL_SLUGS)
    def test_agent_creates_crm_lead(self, brain_tenant, slug):
        template = _ensure_template(slug)
        instance = create_agent_instance(brain_tenant, template, status="active")
        update_agent_settings(instance, business_name="Brain Test Co")
        contact = find_or_create_contact(brain_tenant, name=f"Lead {slug}", email=f"{slug}@test.com")
        conversation = find_or_create_conversation(brain_tenant, contact, agent_instance=instance)

        agent_cls = load_agent_class(slug)
        agent = agent_cls(instance, provider=MockAIProvider())
        message = AGENT_TEST_MESSAGES.get(slug, "Hello, my email is lead@test.com")
        result = agent.run(message, conversation)
        assert result.lead_id
        assert Lead.objects.filter(pk=result.lead_id, agent_instance=instance).exists()


@pytest.mark.django_db
class TestSafetyHandoff:
    def test_clinic_urgent_handoff(self, brain_tenant):
        template = _ensure_template("clinic-agent")
        instance = create_agent_instance(brain_tenant, template, status="active")
        contact = find_or_create_contact(brain_tenant, name="Urgent Patient")
        conversation = find_or_create_conversation(brain_tenant, contact, agent_instance=instance)
        from apps.agent_modules.clinic_agent.agent import ClinicReceptionistAgent

        agent = ClinicReceptionistAgent(instance, provider=MockAIProvider())
        result = agent.run("I have severe chest pain and can't breathe", conversation)
        assert result.should_handoff is True

    def test_finance_tax_handoff(self, brain_tenant):
        template = _ensure_template("finance-agent")
        instance = create_agent_instance(brain_tenant, template, status="active")
        contact = find_or_create_contact(brain_tenant, name="Tax Client")
        conversation = find_or_create_conversation(brain_tenant, contact, agent_instance=instance)
        from apps.agent_modules.finance_agent.agent import FinanceAssistantAgent

        agent = FinanceAssistantAgent(instance, provider=MockAIProvider())
        result = agent.run("I need tax advice on my corporate return filing", conversation)
        assert result.should_handoff is True

    def test_all_agents_deployable(self, client, db):
        from apps.accounts.models import User, UserRole

        tenant = create_tenant(name="Deploy All Co")
        User.objects.create_user(
            email="deployall@test.com",
            password="TestPass123!",
            tenant=tenant,
            role=UserRole.OWNER,
        )
        client.login(username="deployall@test.com", password="TestPass123!")
        for slug in ALL_SLUGS:
            _ensure_template(slug)
            response = client.post(f"/agents/templates/{slug}/deploy/")
            assert response.status_code == 302
