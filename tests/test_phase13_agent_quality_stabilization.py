"""Phase 13 tests: agent quality stabilization and scenario audit."""
import subprocess
import sys
from pathlib import Path

import pytest

from apps.agent_engine.demo_scenarios import SCENARIOS
from apps.agent_engine.domain_intents import get_domain_for_slug
from apps.agent_engine.intent_normalizer import normalize_intent
from apps.agent_engine.services.scenario_runner import run_scenario
from apps.agents.models import AgentTemplate
from apps.agents.services import create_agent_instance
from apps.agent_modules.registry import list_implemented_slugs
from apps.tenants.models import Tenant
from apps.tenants.services import create_tenant


class TestScenarioLibrary:
    def test_at_least_60_scenarios(self):
        assert len(SCENARIOS) >= 60

    def test_no_missing_expected_intent(self):
        for scenario in SCENARIOS:
            assert scenario.expected_intent, f"{scenario.id} missing expected_intent"


@pytest.mark.django_db
class TestScenarioRunnerNormalization:
    def test_scenario_runner_uses_normalized_intents(self, db):
        tenant = create_tenant(name="Norm Co")
        template = AgentTemplate.objects.create(
            slug="finance-agent",
            name="Finance",
            description="F",
            category="F",
            is_implemented=True,
        )
        agent = create_agent_instance(tenant, template, status="active")
        scenario = next(s for s in SCENARIOS if s.id == "fin-tax")
        result = run_scenario(agent, scenario)
        domain = get_domain_for_slug(scenario.template_slug)
        assert result.normalized_intent == normalize_intent(result.intent, domain)
        assert result.should_handoff is True
        intent_check = next(c for c in result.checks if c.name == "intent_matched")
        assert intent_check.status in ("pass", "accepted")

    def test_clinic_urgent_handoff(self, db):
        tenant = create_tenant(name="Clinic Co")
        template = AgentTemplate.objects.create(
            slug="clinic-agent",
            name="Clinic",
            description="C",
            category="C",
            is_implemented=True,
        )
        agent = create_agent_instance(tenant, template, status="active")
        scenario = next(s for s in SCENARIOS if s.id == "clinic-urgent")
        result = run_scenario(agent, scenario)
        assert result.should_handoff is True

    def test_ecommerce_refund_handoff(self, db):
        tenant = create_tenant(name="Eco Co")
        template = AgentTemplate.objects.create(
            slug="ecommerce-agent",
            name="Ecom",
            description="E",
            category="E",
            is_implemented=True,
        )
        agent = create_agent_instance(tenant, template, status="active")
        scenario = next(s for s in SCENARIOS if s.id == "eco-guarantee")
        result = run_scenario(agent, scenario)
        assert result.should_handoff is True


@pytest.mark.django_db
class TestAgentQualityAudit:
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
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "Passed:   60" in proc.stdout
        assert "Warnings: 0" in proc.stdout
        assert "Failed:   0" in proc.stdout
