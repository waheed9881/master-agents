"""Unified settings URL routes."""
from django.contrib.auth import views as auth_views
from django.urls import path

from apps.accounts import team_views
from apps.tenants import settings_views

app_name = "settings"

urlpatterns = [
    path("", settings_views.settings_home_view, name="index"),
    path("workspace/", settings_views.workspace_settings_view, name="workspace"),
    path("team/", team_views.team_list_view, name="team"),
    path("team/invite/", team_views.team_invite_view, name="team-invite"),
    path("team/<int:user_id>/edit/", team_views.team_edit_view, name="team-edit"),
    path("roles/", settings_views.roles_permissions_view, name="roles"),
    path("plan/", settings_views.plan_view, name="plan"),
    path("plan/change/", settings_views.plan_change_view, name="plan-change"),
    path("usage/", settings_views.usage_dashboard_view, name="usage"),
    path("demo-tools/", settings_views.demo_tools_view, name="demo-tools"),
    path("security/", settings_views.security_view, name="security"),
    path(
        "security/password/",
        auth_views.PasswordChangeView.as_view(
            template_name="settings/password_change.html",
            success_url="/settings/security/",
        ),
        name="password-change",
    ),
    path("audit-logs/", settings_views.audit_logs_view, name="audit-logs"),
]
