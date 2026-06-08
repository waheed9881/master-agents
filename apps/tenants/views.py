from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.analytics.selectors import get_agent_engine_counts, get_recent_activity_rows
from apps.analytics.services import AnalyticsService
from apps.agent_engine.qa_status import PRODUCT_VERSION, SCENARIO_AUDIT_PASSED, SCENARIO_COUNT
from apps.tenants.security_status import get_security_dashboard_context


@login_required
def dashboard_view(request):
    """Main SaaS dashboard landing page."""
    stats = {
        "total_leads": 0,
        "hot_leads": 0,
        "conversations": 0,
        "conversations_today": 0,
        "conversations_today_hint": "0 today",
        "agent_count": 0,
        "ai_messages_sent": 0,
        "total_agent_runs": 0,
        "total_tokens": 0,
        "estimated_cost": 0,
    }
    recent_leads = []
    recent_conversations = []
    security_summary = {"status": "PASS", "blocker_count": 0}

    if request.tenant:
        overview_month = AnalyticsService.get_overview_metrics(request.tenant, "last_30_days")
        overview_today = AnalyticsService.get_overview_metrics(request.tenant, "today")
        engine = get_agent_engine_counts(request.tenant, "last_30_days")
        activity = get_recent_activity_rows(request.tenant, "last_30_days")
        sec = get_security_dashboard_context(request.user)

        blocker_count = len(sec.get("production_blockers", []))
        warn_cards = sum(1 for c in sec.get("security_cards", []) if c.get("status") == "WARN")
        fail_cards = sum(1 for c in sec.get("security_cards", []) if c.get("status") == "FAIL")
        if fail_cards:
            sec_status = "FAIL"
        elif warn_cards or blocker_count:
            sec_status = "WARN"
        else:
            sec_status = "PASS"

        security_summary = {
            "status": sec_status,
            "blocker_count": blocker_count,
            "mock_ai": getattr(settings, "AI_PROVIDER", "mock") == "mock",
            "integrations_mock": getattr(settings, "INTEGRATIONS_MOCK_MODE", True),
        }

        conv_today = overview_today["total_conversations"]
        stats = {
            "total_leads": overview_month["total_leads"],
            "hot_leads": overview_month["hot_leads"],
            "conversations": overview_month["total_conversations"],
            "conversations_today": conv_today,
            "conversations_today_hint": f"{conv_today} today",
            "agent_count": overview_month["agent_count"],
            "ai_messages_sent": overview_month["ai_messages_sent"],
            "total_agent_runs": overview_month["total_agent_runs"],
            "total_tokens": engine.get("total_tokens_used", 0),
            "estimated_cost": engine.get("estimated_cost", 0),
        }
        recent_leads = activity.get("leads", [])[:5]
        recent_conversations = activity.get("conversations", [])[:5]

    context = {
        "page_title": "Dashboard",
        "active_nav": "dashboard",
        "stats": stats,
        "recent_leads": recent_leads,
        "recent_conversations": recent_conversations,
        "security_summary": security_summary,
        "product_version": PRODUCT_VERSION,
        "scenario_audit": f"{SCENARIO_AUDIT_PASSED}/{SCENARIO_COUNT}",
        "first_agent": request.tenant.agent_instances.filter(status="active").first() if request.tenant else None,
    }
    return render(request, "dashboard/index.html", context)
