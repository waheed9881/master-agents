"""Phase 9 tests: docs, CI, environment checks, deployment readiness."""
import subprocess
import sys
from pathlib import Path

import pytest
from django.core.management import call_command

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_DOCS = [
    "MVP_SCOPE.md",
    "ARCHITECTURE.md",
    "DATABASE_SCHEMA.md",
    "AGENT_ENGINE.md",
    "API_ENDPOINTS.md",
    "INTEGRATIONS.md",
    "KNOWLEDGE_BASE.md",
    "ANALYTICS.md",
    "DEPLOYMENT.md",
    "SECURITY.md",
    "QA_CHECKLIST.md",
    "RUNBOOK.md",
    "TROUBLESHOOTING.md",
    "RELEASE_NOTES.md",
]

REQUIRED_ENV_VARS = [
    "SECRET_KEY",
    "DATABASE_URL",
    "REDIS_URL",
    "AI_PROVIDER",
    "META_VERIFY_TOKEN",
    "INTEGRATIONS_MOCK_MODE",
]


class TestDocumentation:
    def test_docs_folder_exists(self):
        docs_dir = ROOT / "docs"
        assert docs_dir.is_dir()

    @pytest.mark.parametrize("filename", REQUIRED_DOCS)
    def test_doc_file_exists(self, filename):
        path = ROOT / "docs" / filename
        assert path.is_file(), f"Missing doc: {filename}"
        assert path.stat().st_size > 100, f"Doc too short: {filename}"


class TestEnvExample:
    def test_env_example_exists(self):
        assert (ROOT / ".env.example").is_file()

    @pytest.mark.parametrize("var_name", REQUIRED_ENV_VARS)
    def test_env_example_includes_required_vars(self, var_name):
        content = (ROOT / ".env.example").read_text(encoding="utf-8")
        assert var_name in content, f".env.example missing {var_name}"


class TestEnvironmentCheckScript:
    def test_check_environment_script_exists(self):
        assert (ROOT / "scripts" / "check_environment.py").is_file()

    def test_check_environment_script_runs(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "check_environment.py")],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout + result.stderr
        assert "Environment Check" in output
        assert result.returncode in (0, 1)


class TestDeploymentDocs:
    def test_deployment_docs_mention_docker(self):
        content = (ROOT / "docs" / "DEPLOYMENT.md").read_text(encoding="utf-8")
        assert "docker" in content.lower()

    def test_deployment_docs_mention_migrations(self):
        content = (ROOT / "docs" / "DEPLOYMENT.md").read_text(encoding="utf-8")
        assert "migrate" in content.lower()


class TestSecurityDocs:
    def test_security_docs_mention_secrets(self):
        content = (ROOT / "docs" / "SECURITY.md").read_text(encoding="utf-8")
        assert "SECRET_KEY" in content or "secret" in content.lower()

    def test_security_docs_mention_webhook_signatures(self):
        content = (ROOT / "docs" / "SECURITY.md").read_text(encoding="utf-8")
        assert "signature" in content.lower()


class TestCIWorkflow:
    def test_ci_workflow_exists(self):
        path = ROOT / ".github" / "workflows" / "ci.yml"
        assert path.is_file()

    def test_ci_workflow_runs_tests(self):
        content = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        assert "pytest" in content
        assert "postgres" in content.lower()


class TestDjangoCheck:
    def test_manage_check_passes(self):
        call_command("check")

    @pytest.mark.django_db
    def test_check_deploy_ready_command_exists(self):
        call_command("check_deploy_ready")


class TestSmokeTestScript:
    def test_smoke_test_script_exists(self):
        assert (ROOT / "scripts" / "smoke_test.py").is_file()
