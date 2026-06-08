from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def dashboard_view(request):
    """Main SaaS dashboard landing page."""
    from apps.agents.selectors import list_tenant_agents
    from apps.crm.selectors import get_crm_stats
    from apps.inbox.selectors import get_inbox_stats

    agent_count = 0
    crm_stats = {
        "total_leads": 0,
        "hot_leads": 0,
        "conversations": 0,
        "agent_count": 0,
    }

    if request.tenant:
        agent_count = list_tenant_agents(request.tenant).count()
        stats = get_crm_stats(request.tenant)
        inbox_stats = get_inbox_stats(request.tenant)
        crm_stats = {
            "total_leads": stats["total_leads"],
            "hot_leads": stats["hot_leads"],
            "conversations": inbox_stats["total_conversations"],
            "agent_count": agent_count,
        }

    context = {
        "page_title": "Dashboard",
        "active_nav": "dashboard",
        "stats": crm_stats,
    }
    return render(request, "dashboard/index.html", context)
