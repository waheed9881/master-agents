"""Phase 17 tests: UI polish, demo center, report, launch assets."""
import subprocess
import sys
from pathlib import Path

import pytest

from apps.agent_engine.qa_status import DOCUMENTED_TEST_COUNT, SCENARIO_AUDIT_PASSED, SCENARIO_COUNT
from apps.accounts.models import User, UserRole
from apps.tenants.services import create_tenant

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def demo_ui_setup(client, db):
    tenant = create_tenant(name="Demo UI Co")
    User.objects.create_user(
        email="owner@demo-ui.test",
        password="TestPass123!",
        tenant=tenant,
        role=UserRole.OWNER,
        full_name="Demo Owner",
    )
    client.login(username="owner@demo-ui.test", password="TestPass123!")
    return client, tenant


@pytest.mark.django_db
class TestPhase17Pages:
    def test_dashboard_loads(self, demo_ui_setup):
        client, _ = demo_ui_setup
        response = client.get("/dashboard/")
        assert response.status_code == 200
        assert b"Quick actions" in response.content
        assert b"Demo Center" in response.content

    def test_demo_center_loads(self, demo_ui_setup):
        client, _ = demo_ui_setup
        response = client.get("/demo/")
        assert response.status_code == 200
        assert b"15-minute demo" in response.content
        assert b"30-minute demo" in response.content

    def test_demo_report_loads(self, demo_ui_setup):
        client, _ = demo_ui_setup
        response = client.get("/demo/report/")
        assert response.status_code == 200
        assert b"Print / Save as PDF" in response.content
        assert str(DOCUMENTED_TEST_COUNT).encode() in response.content
        assert str(SCENARIO_AUDIT_PASSED).encode() in response.content
        assert str(SCENARIO_COUNT).encode() in response.content

    def test_agents_gallery_loads(self, demo_ui_setup):
        client, _ = demo_ui_setup
        response = client.get("/agents/")
        assert response.status_code == 200
        assert b"Brain Active" in response.content

    def test_settings_security_loads(self, demo_ui_setup):
        client, _ = demo_ui_setup
        response = client.get("/settings/security/")
        assert response.status_code == 200

    def test_settings_audit_logs_loads(self, demo_ui_setup):
        client, _ = demo_ui_setup
        response = client.get("/settings/audit-logs/")
        assert response.status_code == 200


class TestPhase17DocsAndScripts:
    def test_client_demo_script_exists(self):
        path = ROOT / "docs" / "CLIENT_DEMO_SCRIPT.md"
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "15-minute demo" in text
        assert "30-minute demo" in text
        assert "/demo/report/" in text

    def test_local_launch_docs_exist(self):
        path = ROOT / "docs" / "LOCAL_LAUNCH.md"
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "run_local_demo.bat" in text
        assert "admin@example.com" in text

    def test_local_launch_scripts_exist(self):
        for name in (
            "run_local_demo.bat",
            "run_local_checks.bat",
            "run_local_demo.ps1",
            "run_local_checks.ps1",
        ):
            assert (ROOT / name).exists(), f"Missing {name}"

    def test_demo_report_contains_metrics(self, demo_ui_setup):
        client, _ = demo_ui_setup
        response = client.get("/demo/report/")
        assert b"Scenario audit" in response.content
        assert b"Production limitations" in response.content
