"""Phase 11 tests: agent playground."""
import pytest

from apps.accounts.models import User, UserRole
from apps.agent_engine.models import AgentRun
from apps.agents.models import AgentTemplate
from apps.agents.services import create_agent_instance, update_agent_settings
from apps.tenants.services import create_tenant


@pytest.fixture
def playground_setup(client, db):
    tenant = create_tenant(name="Playground Co")
    User.objects.create_user(
        email="playground@test.com",
        password="TestPass123!",
        full_name="Playground Tester",
        tenant=tenant,
        role=UserRole.OWNER,
    )
    template = AgentTemplate.objects.create(
        name="Real Estate Agent",
        slug="real-estate-agent",
        description="RE",
        category="Real Estate",
        is_implemented=True,
    )
    agent = create_agent_instance(tenant, template, status="active")
    update_agent_settings(agent, business_name="Playground Realty")
    client.login(username="playground@test.com", password="TestPass123!")
    return client, tenant, agent


@pytest.mark.django_db
class TestAgentPlayground:
    def test_playground_page_loads(self, playground_setup):
        client, _, agent = playground_setup
        response = client.get(f"/agents/instances/{agent.pk}/playground/")
        assert response.status_code == 200
        assert b"Playground" in response.content

    def test_playground_returns_intent_and_reply(self, playground_setup):
        client, tenant, agent = playground_setup
        response = client.post(
            f"/agents/instances/{agent.pk}/playground/",
            {
                "channel": "web_chat",
                "message_text": "I want a villa downtown with budget $500k",
            },
        )
        assert response.status_code == 200
        assert b"Actual result" in response.content or b"Quality checks" in response.content
        assert AgentRun.objects.filter(tenant=tenant, agent_instance=agent).exists()

    def test_playground_whatsapp_mock_channel(self, playground_setup):
        client, tenant, agent = playground_setup
        response = client.post(
            f"/agents/instances/{agent.pk}/playground/",
            {
                "channel": "whatsapp_mock",
                "message_text": "Hello, property inquiry for apartment",
            },
        )
        assert response.status_code == 200
        assert AgentRun.objects.filter(tenant=tenant).exists()

    def test_instance_detail_shows_brain_active(self, playground_setup):
        client, _, agent = playground_setup
        response = client.get(f"/agents/instances/{agent.pk}/")
        assert response.status_code == 200
        assert b"Brain Active" in response.content
        assert b"Playground" in response.content
