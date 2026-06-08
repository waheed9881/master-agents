"""Phase 12 tests: Demo Center page."""
import pytest

from apps.accounts.models import User, UserRole
from apps.agent_engine.demo_scenarios import scenario_count_by_slug
from apps.agent_modules.registry import list_implemented_slugs
from apps.agents.models import AgentTemplate
from apps.agents.services import create_agent_instance
from apps.tenants.services import create_tenant


@pytest.fixture
def demo_center_setup(client, db):
    tenant = create_tenant(name="Demo Center Co")
    User.objects.create_user(
        email="democenter@test.com",
        password="TestPass123!",
        tenant=tenant,
        role=UserRole.OWNER,
    )
    for slug in list_implemented_slugs():
        template, _ = AgentTemplate.objects.get_or_create(
            slug=slug,
            defaults={"name": slug, "description": "T", "category": "T", "is_implemented": True},
        )
        template.is_implemented = True
        template.save()
        if not tenant.agent_instances.filter(template=template).exists():
            create_agent_instance(tenant, template, status="active")
    client.login(username="democenter@test.com", password="TestPass123!")
    return client, tenant


@pytest.mark.django_db
class TestDemoCenter:
    def test_demo_center_page_loads(self, demo_center_setup):
        client, _ = demo_center_setup
        response = client.get("/demo/")
        assert response.status_code == 200
        assert b"Demo Center" in response.content

    def test_demo_center_shows_all_agents(self, demo_center_setup):
        client, tenant = demo_center_setup
        response = client.get("/demo/")
        assert response.status_code == 200
        deployed = tenant.agent_instances.count()
        assert deployed == 10
        assert b"scenario" in response.content.lower() or b"Playground" in response.content

    def test_scenario_library_has_five_per_agent(self):
        counts = scenario_count_by_slug()
        for slug in list_implemented_slugs():
            assert counts.get(slug, 0) >= 5, f"{slug} has fewer than 5 scenarios"

    def test_local_demo_guide_exists(self):
        from pathlib import Path

        guide = Path(__file__).resolve().parent.parent / "docs" / "LOCAL_DEMO_GUIDE.md"
        assert guide.exists()
        content = guide.read_text(encoding="utf-8")
        assert "admin@example.com" in content
        assert "playground" in content.lower()
