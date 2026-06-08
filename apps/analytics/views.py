from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render

from apps.analytics import selectors
from apps.analytics.services import AnalyticsService


@login_required
def analytics_dashboard_view(request):
    if not request.tenant:
        raise Http404("No tenant")

    range_key = request.GET.get("range", selectors.DEFAULT_RANGE)
    if range_key not in selectors.VALID_RANGES:
        range_key = selectors.DEFAULT_RANGE

    dashboard = AnalyticsService.get_full_dashboard(request.tenant, range_key)

    return render(
        request,
        "analytics/dashboard.html",
        {
            "page_title": "Analytics",
            "active_nav": "analytics",
            "range_key": range_key,
            "range_choices": [
                ("today", "Today"),
                ("last_7_days", "Last 7 days"),
                ("last_30_days", "Last 30 days"),
                ("all_time", "All time"),
            ],
            "dashboard": dashboard,
        },
    )
