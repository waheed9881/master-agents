"""Phase 14 tests: AI provider settings UI and API."""
import pytest

from apps.accounts.models import User, UserRole
from apps.agents.models import AgentTemplate
from apps.agents.services import create_agent_instance
from apps.agent_engine.services.provider_settings import get_provider_status
from apps.tenants.services import create_tenant


@pytest.fixture
def provider_setup(client, db):
    tenant = create_tenant(name="Provider Co")
    User.objects.create_user(
        email="provider@test.com",
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
    agent = create_agent_instance(tenant, template, status="active")
    client.login(username="provider@test.com", password="TestPass123!")
    return client, tenant, agent


@pytest.mark.django_db
class TestAIProviderSettings:
    def test_provider_status_mock(self, db):
        status = get_provider_status("mock")
        assert status["provider"] == "mock"
        assert status["available"] is True
        assert status["api_key_configured"] is True

    def test_provider_status_endpoint(self, provider_setup):
        client, _, _ = provider_setup
        response = client.get("/api/agent-engine/providers/status/")
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "mock"
        assert "api_key_configured" in data
        assert "OPENAI_API_KEY" not in str(data)

    def test_provider_test_endpoint_mock(self, provider_setup):
        client, _, agent = provider_setup
        response = client.post(
            "/api/agent-engine/providers/test/",
            data={
                "provider": "mock",
                "agent_instance_id": agent.pk,
                "message_text": "Hello, how much does it cost?",
            },
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "mock"
        assert data["reply"]
        assert data["structured_output_valid"] is True
        assert data["safety_status"] in ("safe", "flagged")

    def test_settings_ui_loads(self, provider_setup):
        client, _, _ = provider_setup
        response = client.get("/settings/ai-providers/")
        assert response.status_code == 200
        assert b"AI Provider Settings" in response.content

    def test_demo_center_shows_provider_status(self, provider_setup):
        client, _, _ = provider_setup
        response = client.get("/demo/")
        assert response.status_code == 200
        assert b"Mock" in response.content or b"mock" in response.content
