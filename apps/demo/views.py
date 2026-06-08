from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render

from apps.agent_engine.demo_scenarios import scenario_count_by_slug
from apps.agent_engine.qa_status import DOCUMENTED_TEST_COUNT, PHASE_LABEL, SCENARIO_COUNT
from apps.agent_engine.services.provider_settings import get_provider_status
from apps.agent_modules.registry import list_implemented_slugs
from apps.agents import selectors
from apps.analytics.selectors import get_agent_engine_counts, DEFAULT_RANGE


@login_required
def demo_center_view(request):
    """Local demo control room."""
    if not request.tenant:
        raise Http404("No tenant")

    agents = selectors.list_tenant_agents(request.tenant).select_related("template")
    scenario_counts = scenario_count_by_slug()
    agent_rows = []
    for agent in agents:
        slug = agent.template.slug
        agent_rows.append({
            "instance": agent,
            "scenario_count": scenario_counts.get(slug, 0),
            "brain_active": slug in list_implemented_slugs(),
        })

    implemented_count = len(list_implemented_slugs())
    provider_status = get_provider_status()
    agent_engine_stats = get_agent_engine_counts(request.tenant, DEFAULT_RANGE)

    return render(
        request,
        "demo/center.html",
        {
            "page_title": "Demo Center",
            "active_nav": "demo",
            "agent_rows": agent_rows,
            "implemented_count": implemented_count,
            "mock_ai": getattr(settings, "AI_PROVIDER", "mock") == "mock",
            "ai_provider": provider_status["provider"],
            "fallback_provider": provider_status["fallback_provider"],
            "provider_key_missing": not provider_status["api_key_configured"] and provider_status["provider"] != "mock",
            "agent_engine_stats": agent_engine_stats,
            "integrations_mock": getattr(settings, "INTEGRATIONS_MOCK_MODE", True),
            "documented_test_count": DOCUMENTED_TEST_COUNT,
            "phase_label": PHASE_LABEL,
            "scenario_count": SCENARIO_COUNT,
            "quality_audit_target": "60 passed / 0 warnings / 0 failed",
        },
    )
