"""Phase 16 tests: audit logs, security dashboard, password change."""
import pytest
from django.core.management import call_command
from django.test import Client

from apps.accounts.models import User, UserRole
from apps.integrations.forms import ChannelAccountForm
from apps.integrations.services.channel_service import create_channel_account, update_channel_account
from apps.inbox.models import ChannelType
from apps.tenants.models import AuditLog
from apps.tenants.services import create_tenant


@pytest.fixture
def security_setup(db):
    tenant = create_tenant(name="Security Co")
    owner = User.objects.create_user(
        email="owner@security.test",
        password="OldPass123!",
        tenant=tenant,
        role=UserRole.OWNER,
        full_name="Owner",
    )
    rep = User.objects.create_user(
        email="rep@security.test",
        password="TestPass123!",
        tenant=tenant,
        role=UserRole.SALES_REP,
        full_name="Rep",
    )
    return tenant, owner, rep


@pytest.mark.django_db
class TestAuditLogs:
    def test_audit_logs_page_owner(self, security_setup):
        _, owner, _ = security_setup
        client = Client()
        client.login(username="owner@security.test", password="OldPass123!")
        response = client.get("/settings/audit-logs/")
        assert response.status_code == 200
        assert b"Audit Logs" in response.content

    def test_audit_logs_denied_sales_rep(self, security_setup):
        _, _, rep = security_setup
        client = Client()
        client.login(username="rep@security.test", password="TestPass123!")
        response = client.get("/settings/audit-logs/")
        assert response.status_code == 403

    def test_integration_credential_update_creates_audit(self, security_setup):
        tenant, owner, _ = security_setup
        form = ChannelAccountForm({
            "channel_type": ChannelType.WHATSAPP,
            "display_name": "Audit Channel",
            "phone_number_id": "123",
            "access_token": "test-token-value",
            "mock_mode": True,
            "is_active": True,
        })
        assert form.is_valid(), form.errors
        account = create_channel_account(tenant, form, user=owner)
        assert AuditLog.objects.filter(action="integration_credential_create").exists()

        form2 = ChannelAccountForm({
            "channel_type": ChannelType.WHATSAPP,
            "display_name": "Audit Channel Updated",
            "phone_number_id": "123",
            "access_token": "new-token-value",
            "mock_mode": True,
            "is_active": True,
        })
        assert form2.is_valid()
        update_channel_account(account, form2, user=owner)
        assert AuditLog.objects.filter(action="integration_credential_update").exists()

    def test_demo_reset_creates_audit(self, security_setup):
        tenant, owner, _ = security_setup
        client = Client()
        client.login(username="owner@security.test", password="OldPass123!")
        response = client.post(
            "/settings/demo-tools/",
            data={"action": "webhooks", "confirm": "RESET"},
        )
        assert response.status_code == 302
        assert AuditLog.objects.filter(action="demo_reset").exists()


@pytest.mark.django_db
class TestSecurityDashboard:
    def test_security_dashboard_loads(self, security_setup):
        client = Client()
        client.login(username="owner@security.test", password="OldPass123!")
        response = client.get("/settings/security/")
        assert response.status_code == 200
        assert b"Security" in response.content
        assert b"Production Blockers" in response.content

    def test_password_change_works(self, security_setup):
        client = Client()
        client.login(username="owner@security.test", password="OldPass123!")
        response = client.post(
            "/settings/security/password/",
            data={
                "old_password": "OldPass123!",
                "new_password1": "NewSecure456!",
                "new_password2": "NewSecure456!",
            },
        )
        assert response.status_code == 302
        owner = User.objects.get(email="owner@security.test")
        assert owner.check_password("NewSecure456!")
        assert client.login(username="owner@security.test", password="NewSecure456!")

    def test_security_audit_command_runs(self):
        call_command("security_audit")
