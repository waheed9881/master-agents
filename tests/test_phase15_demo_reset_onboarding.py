"""Phase 15 tests: demo reset tools and onboarding wizard."""
import pytest

from apps.accounts.models import User, UserRole
from apps.agent_engine.models import AgentRun
from apps.crm.models import Lead
from apps.inbox.models import Conversation
from apps.integrations.models import WebhookEvent
from apps.tenants.demo_reset import reset_safe_demo_data
from apps.tenants.services import create_tenant


@pytest.fixture
def demo_setup(client, db):
    tenant = create_tenant(name="Demo Reset Co")
    User.objects.create_user(
        email="demo@reset.test",
        password="TestPass123!",
        tenant=tenant,
        role=UserRole.OWNER,
    )
    client.login(username="demo@reset.test", password="TestPass123!")
    return client, tenant


@pytest.mark.django_db
class TestDemoResetAndOnboarding:
    def test_demo_tools_page_loads(self, demo_setup):
        client, _ = demo_setup
        response = client.get("/settings/demo-tools/")
        assert response.status_code == 200
        assert b"Demo Tools" in response.content

    def test_safe_reset_clears_data_keeps_tenant(self, demo_setup):
        _, tenant = demo_setup
        user_count = tenant.users.count()
        from apps.agents.models import AgentTemplate
        from apps.agents.services import create_agent_instance
        from apps.crm.models import Contact

        contact = Contact.objects.create(tenant=tenant, name="Test Contact")
        template = AgentTemplate.objects.create(
            slug="sales-closing-agent",
            name="Sales",
            description="S",
            category="S",
            is_implemented=True,
        )
        agent = create_agent_instance(tenant, template, status="active")
        Conversation.objects.create(
            tenant=tenant,
            contact=contact,
            channel_type="web_chat",
            status="open",
        )
        Lead.objects.create(tenant=tenant, contact=contact, title="Test Lead", status="new")
        AgentRun.objects.create(
            tenant=tenant,
            agent_instance=agent,
            input_message="hello",
            intent="test",
        )
        WebhookEvent.objects.create(tenant=tenant, channel_type="whatsapp", payload_json={})

        reset_safe_demo_data(tenant, reseed=False)
        assert Conversation.objects.filter(tenant=tenant).count() == 0
        assert Lead.objects.filter(tenant=tenant).count() == 0
        assert AgentRun.objects.filter(tenant=tenant).count() == 0
        assert WebhookEvent.objects.filter(tenant=tenant).count() == 0
        assert tenant.users.count() == user_count

    def test_onboarding_page_loads(self, demo_setup):
        client, _ = demo_setup
        response = client.get("/onboarding/")
        assert response.status_code == 200
        assert b"Onboarding" in response.content
