#!/usr/bin/env python
"""
Audit agent quality by running all demo scenarios in mock mode.

Usage:
    python scripts/audit_agent_quality.py

Environment:
    AUDIT_AI_PROVIDER=mock (default) — force provider for deterministic audit
"""
import os
import sys

# Force mock provider before Django loads settings (default deterministic audit)
audit_provider = os.environ.get("AUDIT_AI_PROVIDER", "mock")
os.environ["AI_PROVIDER"] = audit_provider

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.conf import settings

settings.AI_PROVIDER = audit_provider

from apps.agent_engine.demo_scenarios import SCENARIOS
from apps.agent_engine.services.scenario_runner import run_scenario
from apps.agents.models import AgentInstance
from apps.tenants.models import Tenant


def audit():
    print("AI Agent OS - Agent Quality Audit")
    print("=" * 40)

    tenant = Tenant.objects.filter(slug="demo-company").first()
    if not tenant:
        print("[FAIL] Demo tenant not found. Run: python scripts/seed_demo_data.py")
        return 1

    passed = 0
    accepted = 0
    warnings = 0
    failed = 0

    for scenario in SCENARIOS:
        agent = AgentInstance.objects.filter(
            tenant=tenant,
            template__slug=scenario.template_slug,
            status="active",
        ).select_related("template").first()

        if not agent:
            print(f"[FAIL] No deployed agent for {scenario.template_slug} ({scenario.id})")
            failed += 1
            continue

        result = run_scenario(agent, scenario, channel=scenario.suggested_channel)

        status_icon = {
            "pass": "PASS",
            "accepted": "ACCEPTED",
            "warn": "WARN",
            "fail": "FAIL",
        }[result.overall]
        print(f"[{status_icon}] {scenario.template_slug} / {scenario.id}: {scenario.title}")

        if result.overall == "pass":
            passed += 1
        elif result.overall == "accepted":
            accepted += 1
        elif result.overall == "warn":
            warnings += 1
            for check in result.checks:
                if check.status == "warn":
                    print(f"       - {check.name}: {check.detail}")
        else:
            failed += 1
            for check in result.checks:
                if check.status == "fail":
                    print(f"       - {check.name}: {check.detail}")

    total = len(SCENARIOS)
    print("=" * 40)
    print(f"Total scenarios: {total}")
    print(f"Passed:   {passed}")
    print(f"Accepted: {accepted}")
    print(f"Warnings: {warnings}")
    print(f"Failed:   {failed}")
    print("=" * 40)

    if failed == 0 and warnings == 0:
        print("Result: PASS")
        return 0
    if failed == 0:
        print("Result: PASS WITH WARNINGS")
        return 0
    print("Result: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(audit())
