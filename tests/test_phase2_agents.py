"""Phase 2 tests: agent templates and instances."""
import pytest
from django.urls import reverse

from apps.accounts.models import User, UserRole
from apps.agents.models import AgentTemplate
from apps.agents.services import create_agent_instance
from apps.tenants.services import create_tenant


@pytest.fixture
def seeded_templates(db):
    """Create minimal template set for tests."""
    templates = [
        AgentTemplate.objects.create(
            name="WhatsApp + Instagram Sales Closing Agent",
            slug="sales-closing-agent",
            description="Sales agent",
            category="Sales",
            priority_label="Build first",
            market_need_score=97,
            tags_json=["PK", "KSA", "USA", "UAE"],
            is_implemented=True,
        ),
        AgentTemplate.objects.create(
            name="Real Estate AI Sales Agent",
            slug="real-estate-agent",
            description="Real estate",
            category="Real Estate",
            market_need_score=88,
            tags_json=["PK", "UAE"],
            is_implemented=False,
        ),
    ]
    return templates


@pytest.fixture
def auth_client(client, db):
    tenant = create_tenant(name="Agent Test Co")
    User.objects.create_user(
        email="agenttest@example.com",
        password="TestPass123!",
        full_name="Agent Tester",
        tenant=tenant,
        role=UserRole.OWNER,
    )
    client.login(username="agenttest@example.com", password="TestPass123!")
    return client, tenant


@pytest.mark.django_db
class TestAgentTemplates:
    def test_gallery_requires_auth(self, client):
        response = client.get(reverse("agents:gallery"))
        assert response.status_code == 302

    def test_gallery_shows_templates(self, auth_client, seeded_templates):
        client, _ = auth_client
        response = client.get(reverse("agents:gallery"))
        assert response.status_code == 200
        assert b"Sales Closing Agent" in response.content
        assert b"Real Estate" in response.content

    def test_template_detail_page(self, auth_client, seeded_templates):
        client, _ = auth_client
        response = client.get(reverse("agents:detail", kwargs={"slug": "sales-closing-agent"}))
        assert response.status_code == 200
        assert b"Build first" in response.content
        assert b"97" in response.content

    def test_api_list_templates(self, auth_client, seeded_templates):
        client, _ = auth_client
        response = client.get("/api/agent-templates/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        sales = next(t for t in data if t["slug"] == "sales-closing-agent")
        assert sales["market_need_score"] == 97
        assert sales["is_implemented"] is True


@pytest.mark.django_db
class TestAgentInstance:
    def test_create_sales_agent_instance(self, auth_client, seeded_templates):
        client, tenant = auth_client
        template = AgentTemplate.objects.get(slug="sales-closing-agent")
        instance = create_agent_instance(tenant=tenant, template=template)
        assert instance.name == template.name
        assert instance.settings.qualification_questions_json

    def test_api_create_agent(self, auth_client, seeded_templates):
        client, _ = auth_client
        template = AgentTemplate.objects.get(slug="sales-closing-agent")
        response = client.post(
            "/api/agents/",
            {"template_id": template.pk},
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["template_slug"] == "sales-closing-agent"

    def test_api_rejects_unimplemented_template(self, auth_client, seeded_templates):
        client, _ = auth_client
        template = AgentTemplate.objects.get(slug="real-estate-agent")
        response = client.post(
            "/api/agents/",
            {"template_id": template.pk},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_deploy_via_form(self, auth_client, seeded_templates):
        client, tenant = auth_client
        response = client.post(
            reverse("agents:deploy", kwargs={"slug": "sales-closing-agent"}),
        )
        assert response.status_code == 302
        assert tenant.agent_instances.filter(template__slug="sales-closing-agent").exists()
