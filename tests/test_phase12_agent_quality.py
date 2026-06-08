"""Phase 12 tests: agent quality audit script."""
import subprocess
import sys
from pathlib import Path

import pytest

from apps.agent_engine.demo_scenarios import SCENARIOS
from apps.agent_engine.services.scenario_runner import run_scenario
from apps.agents.models import AgentTemplate
from apps.agents.services import create_agent_instance
from apps.agent_modules.registry import list_implemented_slugs
from apps.tenants.models import Tenant
from apps.tenants.services import create_tenant


@pytest.mark.django_db
class TestAgentQualityAudit:
    def test_scenario_runner_produces_checks(self, db):
        tenant = create_tenant(name="Quality Co")
        template = AgentTemplate.objects.create(
            slug="sales-closing-agent",
            name="Sales",
            description="S",
            category="S",
            is_implemented=True,
        )
        agent = create_agent_instance(tenant, template, status="active")
        scenario = SCENARIOS[0]
        result = run_scenario(agent, scenario)
        assert result.reply
        assert result.agent_run_id
        assert result.intent
        assert len(result.checks) >= 5

    def test_audit_script_runs(self, db):
        tenant, _ = Tenant.objects.get_or_create(
            slug="demo-company",
            defaults={"name": "Demo Company", "country": "USA"},
        )
        for slug in list_implemented_slugs():
            template, _ = AgentTemplate.objects.get_or_create(
                slug=slug,
                defaults={"name": slug, "description": "T", "category": "T", "is_implemented": True},
            )
            if not tenant.agent_instances.filter(template=template).exists():
                create_agent_instance(tenant, template, status="active")

        root = Path(__file__).resolve().parent.parent
        proc = subprocess.run(
            [sys.executable, str(root / "scripts" / "audit_agent_quality.py")],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=180,
        )
        assert proc.returncode in (0, 1)
        assert "Agent Quality Audit" in proc.stdout
        assert "Total scenarios:" in proc.stdout
