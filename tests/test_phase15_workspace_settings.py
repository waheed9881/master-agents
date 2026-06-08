"""Phase 15 tests: workspace settings and settings home."""
import pytest

from apps.accounts.models import User, UserRole
from apps.tenants.models import Tenant
from apps.tenants.services import create_tenant


@pytest.fixture
def settings_setup(client, db):
    tenant = create_tenant(name="Settings Co")
    User.objects.create_user(
        email="owner@settings.test",
        password="TestPass123!",
        tenant=tenant,
        role=UserRole.OWNER,
        full_name="Owner User",
    )
    client.login(username="owner@settings.test", password="TestPass123!")
    return client, tenant


@pytest.mark.django_db
class TestWorkspaceSettings:
    def test_settings_home_loads(self, settings_setup):
        client, _ = settings_setup
        response = client.get("/settings/")
        assert response.status_code == 200
        assert b"Settings" in response.content
        assert b"Workspace" in response.content

    def test_workspace_settings_loads(self, settings_setup):
        client, _ = settings_setup
        response = client.get("/settings/workspace/")
        assert response.status_code == 200
        assert b"Workspace Settings" in response.content

    def test_workspace_settings_updates_tenant(self, settings_setup):
        client, tenant = settings_setup
        response = client.post(
            "/settings/workspace/",
            data={
                "name": "Updated Co",
                "slug": tenant.slug,
                "country": "UK",
                "industry": "SaaS",
                "timezone": "Europe/London",
                "default_currency": "GBP",
                "business_description": "We sell AI agents.",
                "support_email": "help@updated.test",
                "support_phone": "+44123456789",
            },
        )
        assert response.status_code == 302
        tenant.refresh_from_db()
        assert tenant.name == "Updated Co"
        assert tenant.country == "UK"
        assert tenant.business_description == "We sell AI agents."
