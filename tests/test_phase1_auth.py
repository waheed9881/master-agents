"""Phase 1 tests: auth and tenant foundation."""
import pytest
from django.urls import reverse

from apps.accounts.models import User, UserRole
from apps.tenants.models import Tenant
from apps.tenants.services import create_tenant


@pytest.mark.django_db
class TestTenantCreation:
    def test_create_tenant(self):
        tenant = create_tenant(name="Test Corp", country="PK")
        assert tenant.slug == "test-corp"
        assert tenant.country == "PK"


@pytest.mark.django_db
class TestUserLogin:
    def test_login_page_loads(self, client):
        response = client.get(reverse("accounts:login"))
        assert response.status_code == 200
        assert b"Sign in" in response.content or b"Welcome back" in response.content

    def test_login_success(self, client):
        tenant = create_tenant(name="Login Test Co")
        User.objects.create_user(
            email="test@example.com",
            password="TestPass123!",
            full_name="Test User",
            tenant=tenant,
            role=UserRole.OWNER,
        )
        response = client.post(
            reverse("accounts:login"),
            {"email": "test@example.com", "password": "TestPass123!"},
        )
        assert response.status_code == 302
        assert response.url.endswith("/dashboard/")

    def test_dashboard_requires_auth(self, client):
        response = client.get(reverse("dashboard:index"))
        assert response.status_code == 302
        assert "login" in response.url

    def test_api_login(self, client):
        tenant = create_tenant(name="API Test Co")
        User.objects.create_user(
            email="api@example.com",
            password="ApiPass123!",
            full_name="API User",
            tenant=tenant,
        )
        response = client.post(
            "/api/auth/login/",
            {"email": "api@example.com", "password": "ApiPass123!"},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["email"] == "api@example.com"
