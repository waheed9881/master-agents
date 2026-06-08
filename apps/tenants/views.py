from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.analytics.services import AnalyticsService


@login_required
def dashboard_view(request):
    """Main SaaS dashboard landing page."""
    stats = {
        "total_leads": 0,
        "hot_leads": 0,
        "conversations": 0,
        "agent_count": 0,
        "ai_messages_sent": 0,
        "total_agent_runs": 0,
    }

    if request.tenant:
        overview = AnalyticsService.get_overview_metrics(request.tenant, "last_30_days")
        stats = {
            "total_leads": overview["total_leads"],
            "hot_leads": overview["hot_leads"],
            "conversations": overview["total_conversations"],
            "agent_count": overview["agent_count"],
            "ai_messages_sent": overview["ai_messages_sent"],
            "total_agent_runs": overview["total_agent_runs"],
        }

    context = {
        "page_title": "Dashboard",
        "active_nav": "dashboard",
        "stats": stats,
    }
    return render(request, "dashboard/index.html", context)
