"""Phase 18 tests: UAT sessions, checklist, feedback, sign-off."""
import csv
import io
import subprocess
import sys
from pathlib import Path

import pytest

from apps.accounts.models import User, UserRole
from apps.agent_engine.qa_status import SCENARIO_AUDIT_PASSED, SCENARIO_COUNT
from apps.tenants.services import create_tenant
from apps.uat.default_checklist import DEFAULT_CHECKLIST_ITEMS
from apps.uat.models import (
    ChecklistItemStatus,
    FeedbackCategory,
    FeedbackItem,
    FeedbackPriority,
    FeedbackStatus,
    UATSession,
    UATSessionStatus,
)
from apps.uat.services import create_session, sign_off_session, update_checklist_status
from apps.uat.services import UATSignOffError

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def uat_owner_setup(client, db):
    tenant = create_tenant(name="UAT Test Co")
    User.objects.create_user(
        email="owner@uat.test",
        password="TestPass123!",
        tenant=tenant,
        role=UserRole.OWNER,
        full_name="UAT Owner",
    )
    client.login(username="owner@uat.test", password="TestPass123!")
    return client, tenant


@pytest.fixture
def uat_rep_setup(client, db):
    tenant = create_tenant(name="UAT Rep Co")
    User.objects.create_user(
        email="rep@uat.test",
        password="TestPass123!",
        tenant=tenant,
        role=UserRole.SALES_REP,
        full_name="UAT Rep",
    )
    client.login(username="rep@uat.test", password="TestPass123!")
    return client, tenant


@pytest.mark.django_db
class TestPhase18UAT:
    def test_uat_dashboard_loads(self, uat_owner_setup):
        client, _ = uat_owner_setup
        response = client.get("/uat/")
        assert response.status_code == 200
        assert b"UAT and Feedback" in response.content or b"active sessions" in response.content.lower()

    def test_owner_can_create_uat_session(self, uat_owner_setup):
        client, tenant = uat_owner_setup
        response = client.post(
            "/uat/sessions/new/",
            {
                "title": "Client Demo UAT",
                "demo_version": "MVP 1.8",
                "audience": "Client stakeholders",
                "facilitator": "Owner",
                "summary": "First demo run",
            },
        )
        assert response.status_code == 302
        session = UATSession.objects.get(tenant=tenant, title="Client Demo UAT")
        assert session.checklist_items.count() == len(DEFAULT_CHECKLIST_ITEMS)

    def test_default_checklist_seed_creates_items(self, uat_owner_setup):
        _, tenant = uat_owner_setup
        owner = User.objects.get(email="owner@uat.test")
        session = create_session(tenant, title="Seed Test", created_by=owner)
        assert session.checklist_items.count() == len(DEFAULT_CHECKLIST_ITEMS)

    def test_session_detail_loads(self, uat_owner_setup):
        client, tenant = uat_owner_setup
        owner = User.objects.get(email="owner@uat.test")
        session = create_session(tenant, title="Detail Session", created_by=owner)
        response = client.get(f"/uat/sessions/{session.pk}/")
        assert response.status_code == 200
        assert b"Detail Session" in response.content or session.title.encode() in response.content

    def test_checklist_item_can_be_marked_passed_failed(self, uat_owner_setup):
        client, tenant = uat_owner_setup
        owner = User.objects.get(email="owner@uat.test")
        session = create_session(tenant, title="Checklist Session", created_by=owner)
        item = session.checklist_items.first()
        response = client.post(
            f"/uat/sessions/{session.pk}/",
            {
                "action": "update_checklist",
                "item_id": item.pk,
                "status": ChecklistItemStatus.PASSED,
                "notes": "OK",
            },
        )
        assert response.status_code == 302
        item.refresh_from_db()
        assert item.status == ChecklistItemStatus.PASSED

        item2 = session.checklist_items.exclude(pk=item.pk).first()
        client.post(
            f"/uat/sessions/{session.pk}/",
            {
                "action": "update_checklist",
                "item_id": item2.pk,
                "status": ChecklistItemStatus.FAILED,
                "notes": "Broken",
            },
        )
        item2.refresh_from_db()
        assert item2.status == ChecklistItemStatus.FAILED

    def test_feedback_list_loads(self, uat_owner_setup):
        client, _ = uat_owner_setup
        response = client.get("/uat/feedback/")
        assert response.status_code == 200

    def test_feedback_item_can_be_created(self, uat_owner_setup):
        client, tenant = uat_owner_setup
        response = client.post(
            "/uat/feedback/new/",
            {
                "title": "Button misaligned",
                "description": "On agents page",
                "category": FeedbackCategory.UX,
                "priority": FeedbackPriority.MEDIUM,
                "status": FeedbackStatus.OPEN,
                "module_area": "agents",
                "related_url": "/agents/",
            },
        )
        assert response.status_code == 302
        assert FeedbackItem.objects.filter(tenant=tenant, title="Button misaligned").exists()

    def test_feedback_csv_export_works(self, uat_owner_setup):
        client, tenant = uat_owner_setup
        owner = User.objects.get(email="owner@uat.test")
        FeedbackItem.objects.create(
            tenant=tenant,
            title="Export item",
            description="Test export",
            category=FeedbackCategory.BUG,
            priority=FeedbackPriority.LOW,
            status=FeedbackStatus.OPEN,
            module_area="demo",
            created_by=owner,
        )
        response = client.get("/uat/feedback/export.csv")
        assert response.status_code == 200
        assert response["Content-Type"].startswith("text/csv")
        content = response.content.decode("utf-8")
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        assert rows[0][0] == "title"
        assert any("Export item" in row[0] for row in rows[1:])

    def test_uat_report_loads(self, uat_owner_setup):
        client, _ = uat_owner_setup
        response = client.get("/uat/report/")
        assert response.status_code == 200
        assert b"Print / Save as PDF" in response.content

    def test_critical_blockers_prevent_sign_off(self, uat_owner_setup):
        _, tenant = uat_owner_setup
        owner = User.objects.get(email="owner@uat.test")
        session = create_session(tenant, title="Blocked Signoff", created_by=owner)
        FeedbackItem.objects.create(
            tenant=tenant,
            title="Critical bug",
            description="Blocks launch",
            category=FeedbackCategory.PRODUCTION_BLOCKER,
            priority=FeedbackPriority.CRITICAL,
            status=FeedbackStatus.OPEN,
            created_by=owner,
        )
        with pytest.raises(UATSignOffError):
            sign_off_session(session, owner)

    def test_no_critical_blockers_allow_sign_off(self, uat_owner_setup):
        _, tenant = uat_owner_setup
        owner = User.objects.get(email="owner@uat.test")
        session = create_session(tenant, title="Clean Signoff", created_by=owner)
        signed = sign_off_session(session, owner)
        assert signed.status == UATSessionStatus.SIGNED_OFF
        assert signed.signed_off_by_id == owner.pk

    def test_sales_rep_cannot_access_restricted_uat_admin(self, uat_rep_setup):
        client, _ = uat_rep_setup
        assert client.get("/uat/").status_code == 403
        assert client.get("/uat/sessions/new/").status_code == 403
        assert client.get("/uat/report/").status_code == 403
        assert client.get("/uat/feedback/export.csv").status_code == 403

    def test_sales_rep_can_create_feedback(self, uat_rep_setup):
        client, tenant = uat_rep_setup
        response = client.post(
            "/uat/feedback/new/",
            {
                "title": "Rep feedback",
                "description": "From sales rep",
                "category": FeedbackCategory.QUESTION,
                "priority": FeedbackPriority.LOW,
                "module_area": "crm",
            },
        )
        assert response.status_code == 302
        assert FeedbackItem.objects.filter(tenant=tenant, title="Rep feedback").exists()

    def test_demo_center_links_to_uat(self, uat_owner_setup):
        client, _ = uat_owner_setup
        response = client.get("/demo/")
        assert response.status_code == 200
        assert b"UAT dashboard" in response.content or b"/uat/" in response.content
        assert b"Report feedback" in response.content


class TestPhase18ScenarioAudit:
    def test_scenario_audit_constants(self):
        assert SCENARIO_AUDIT_PASSED == SCENARIO_COUNT == 60

    def test_scenario_audit_script(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "audit_agent_quality.py")],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            timeout=120,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        out = result.stdout.lower()
        assert "passed:" in out and "60" in out and "failed:   0" in out
