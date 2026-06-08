"""Demo report context for printable client summary."""
from __future__ import annotations

from django.conf import settings

from apps.agent_engine.demo_scenarios import scenario_count_by_slug
from apps.agent_engine.qa_status import (
    DOCUMENTED_TEST_COUNT,
    PHASE_LABEL,
    PRODUCT_VERSION,
    SCENARIO_AUDIT_PASSED,
    SCENARIO_COUNT,
)
from apps.agent_engine.services.provider_settings import get_provider_status
from apps.agent_modules.registry import list_implemented_slugs
from apps.agents import selectors
from apps.agents.models import AgentTemplate


def get_demo_report_context(request) -> dict:
    tenant = getattr(request, "tenant", None)
    templates = list(AgentTemplate.objects.filter(is_active=True).order_by("category", "name"))
    scenario_counts = scenario_count_by_slug()
    provider_status = get_provider_status()

    agents_list = []
    for template in templates:
        agents_list.append({
            "name": template.name,
            "category": template.category,
            "slug": template.slug,
            "brain_active": template.is_implemented,
            "scenario_count": scenario_counts.get(template.slug, 0),
            "regions": [t for t in (template.tags_json or []) if t in ("PK", "KSA", "USA", "UAE", "Global")],
        })

    deployed_count = 0
    uat_summary = None
    if tenant:
        deployed_count = selectors.list_tenant_agents(tenant).count()
        from apps.uat import selectors as uat_selectors
        from apps.uat.models import UATSessionStatus

        sessions = uat_selectors.sessions_for_tenant(tenant)
        signed_off = sessions.filter(status=UATSessionStatus.SIGNED_OFF).first()
        counts = uat_selectors.feedback_counts(tenant)
        uat_summary = {
            "session_count": sessions.count(),
            "signed_off": signed_off.title if signed_off else None,
            "signed_off_at": signed_off.signed_off_at if signed_off else None,
            "open_feedback": counts.get("open", 0),
            "critical_blockers": counts.get("critical", 0),
        }

    return {
        "page_title": "Demo Report",
        "active_nav": "demo",
        "product_name": "AI Agent OS",
        "product_version": PRODUCT_VERSION,
        "phase_label": PHASE_LABEL,
        "documented_test_count": DOCUMENTED_TEST_COUNT,
        "scenario_count": SCENARIO_COUNT,
        "scenario_audit_passed": SCENARIO_AUDIT_PASSED,
        "agents_list": agents_list,
        "implemented_count": len(list_implemented_slugs()),
        "deployed_count": deployed_count,
        "tenant_name": tenant.name if tenant else "N/A",
        "mock_ai": getattr(settings, "AI_PROVIDER", "mock") == "mock",
        "ai_provider": provider_status["provider"],
        "integrations_mock": getattr(settings, "INTEGRATIONS_MOCK_MODE", True),
        "encryption_configured": bool(getattr(settings, "CREDENTIALS_ENCRYPTION_KEY", "")),
        "rate_limiting_enabled": getattr(settings, "RATE_LIMITING_ENABLED", True),
        "debug_mode": settings.DEBUG,
        "modules_complete": [
            "Auth and multi-tenant workspaces",
            "10 AI agent templates with active brains",
            "CRM (leads, pipeline, tasks)",
            "Unified inbox and web chat",
            "Knowledge base",
            "Analytics dashboard",
            "WhatsApp/Instagram mock integrations",
            "AI provider settings with guardrails",
            "Workspace settings, team roles, plans",
            "Security hardening (encryption, rate limits, audit logs)",
        ],
        "security_features": [
            "Fernet credential encryption (when key configured)",
            "Cache-based rate limiting",
            "Security audit log",
            "Tenant isolation checks",
            "Local backup scripts",
            "Password change UI",
        ],
        "production_limitations": [
            "HTTPS and production hosting not included in local MVP",
            "Mock AI provider by default (rule-based, not live LLM)",
            "Mock Meta integrations by default",
            "No payment gateway or live billing",
            "Manual backups (no scheduled automation)",
            "No APM or error monitoring service",
            "Demo account password must be changed before public demo",
        ],
        "uat_summary": uat_summary,
        "recommended_next_steps": [
            "Deploy to staging with DEBUG=False and strong SECRET_KEY",
            "Set CREDENTIALS_ENCRYPTION_KEY and change demo password",
            "Configure live AI provider if needed for pilot",
            "Schedule automated database backups",
            "Add monitoring (e.g. Sentry) before public launch",
        ],
    }
