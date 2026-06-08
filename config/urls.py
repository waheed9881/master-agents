"""URL configuration for AI Agent OS."""
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path


def root_redirect(request):
    if request.user.is_authenticated:
        return redirect("dashboard:index")
    return redirect("accounts:login")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", root_redirect, name="root"),
    path("", include("apps.accounts.urls")),
    path("dashboard/", include("apps.tenants.urls")),
    path("agents/", include("apps.agents.urls")),
    path("crm/", include("apps.crm.urls")),
    path("inbox/", include("apps.inbox.urls")),
    path("knowledge/", include("apps.knowledge.urls")),
    path("analytics/", include("apps.analytics.urls")),
    path("integrations/", include("apps.integrations.urls")),
    path("api/", include("apps.accounts.api_urls")),
    path("api/", include("apps.agents.api_urls")),
    path("api/", include("apps.crm.api_urls")),
    path("api/", include("apps.inbox.api_urls")),
    path("api/", include("apps.knowledge.api_urls")),
    path("api/", include("apps.analytics.api_urls")),
    path("api/", include("apps.agent_engine.api_urls")),
    path("api/", include("apps.integrations.api_urls")),
    path("api/webhooks/", include("apps.integrations.webhook_urls")),
]
