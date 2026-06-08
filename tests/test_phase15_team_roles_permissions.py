"""Phase 15 tests: team management and role permissions."""
import pytest

from apps.accounts import permissions as perms
from apps.accounts.models import User, UserRole
from apps.accounts.team_services import TeamManagementError, update_team_member
from apps.tenants.services import create_tenant


@pytest.fixture
def team_setup(client, db):
    tenant = create_tenant(name="Team Co")
    owner = User.objects.create_user(
        email="owner@team.test",
        password="TestPass123!",
        tenant=tenant,
        role=UserRole.OWNER,
        full_name="Owner",
    )
    rep = User.objects.create_user(
        email="rep@team.test",
        password="TestPass123!",
        tenant=tenant,
        role=UserRole.SALES_REP,
        full_name="Sales Rep",
    )
    return client, tenant, owner, rep


@pytest.mark.django_db
class TestTeamAndPermissions:
    def test_team_list_loads_for_owner(self, team_setup):
        client, _, owner, _ = team_setup
        client.login(username=owner.email, password="TestPass123!")
        response = client.get("/settings/team/")
        assert response.status_code == 200
        assert b"Team Members" in response.content

    def test_sales_rep_cannot_access_team(self, team_setup):
        client, _, _, rep = team_setup
        client.login(username=rep.email, password="TestPass123!")
        response = client.get("/settings/team/")
        assert response.status_code == 403

    def test_owner_can_create_team_user(self, team_setup):
        client, tenant, owner, _ = team_setup
        from apps.tenants.plan_services import ensure_tenant_subscription, seed_plans

        seed_plans()
        ensure_tenant_subscription(tenant, plan_slug="enterprise")

        client.login(username=owner.email, password="TestPass123!")
        response = client.post(
            "/settings/team/invite/",
            data={
                "email": "new@team.test",
                "full_name": "New Member",
                "role": UserRole.SALES_REP,
            },
        )
        assert response.status_code == 302
        assert User.objects.filter(email="new@team.test", tenant=tenant).exists()

    def test_owner_cannot_deactivate_self_if_last_owner(self, team_setup):
        _, tenant, owner, _ = team_setup
        with pytest.raises(TeamManagementError, match="cannot deactivate"):
            update_team_member(owner, owner, is_active=False)

    def test_permission_helpers(self, team_setup):
        _, _, owner, rep = team_setup
        assert perms.is_owner(owner) is True
        assert perms.is_sales_rep(rep) is True
        assert perms.can_manage_team(owner) is True
        assert perms.can_manage_team(rep) is False
        assert perms.can_view_analytics(rep) is False
        assert perms.can_manage_knowledge(rep) is False
        assert perms.can_use_agent_playground(rep) is True
