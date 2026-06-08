"""Phase 10 tests: release freeze, audit scripts, staging readiness."""
import subprocess
import sys
from pathlib import Path

import pytest
from django.core.management import call_command

ROOT = Path(__file__).resolve().parent.parent

PHASE10_DOCS = [
    "RELEASE_CHECKLIST.md",
    "STAGING_DEPLOYMENT_PLAN.md",
    "FINAL_MVP_ACCEPTANCE_REPORT.md",
]

PHASE10_SCRIPTS = [
    "audit_routes.py",
    "api_smoke_test.py",
]


class TestReleaseDocs:
    @pytest.mark.parametrize("filename", PHASE10_DOCS)
    def test_release_doc_exists(self, filename):
        path = ROOT / "docs" / filename
        assert path.is_file(), f"Missing doc: {filename}"
        assert path.stat().st_size > 200


class TestAuditScripts:
    @pytest.mark.parametrize("script_name", PHASE10_SCRIPTS)
    def test_audit_script_exists(self, script_name):
        assert (ROOT / "scripts" / script_name).is_file()

    def test_audit_routes_script_runs(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "audit_routes.py")],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout + result.stderr
        assert "Route Audit" in output
        assert result.returncode in (0, 1)

    def test_api_smoke_script_runs(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "api_smoke_test.py")],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout + result.stderr
        assert "API Smoke Test" in output
        assert result.returncode in (0, 1)


class TestEnvironmentValidation:
    def test_check_environment_script_runs(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "check_environment.py")],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert "Environment Check" in result.stdout + result.stderr
        assert result.returncode in (0, 1)

    @pytest.mark.django_db
    def test_check_deploy_ready_runs(self):
        call_command("check_deploy_ready")


class TestReadmeAndSecurity:
    def test_readme_mentions_staging_readiness(self):
        content = (ROOT / "README.md").read_text(encoding="utf-8")
        lower = content.lower()
        assert "staging" in lower
        assert "demo" in lower
        assert "phase 10" in lower or "release" in lower or "mvp status" in lower

    def test_security_docs_mention_debug_false(self):
        content = (ROOT / "docs" / "SECURITY.md").read_text(encoding="utf-8")
        assert "DEBUG" in content
        assert "False" in content

    def test_security_docs_mention_secret_key(self):
        content = (ROOT / "docs" / "SECURITY.md").read_text(encoding="utf-8")
        assert "SECRET_KEY" in content
