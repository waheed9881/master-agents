"""Workspace settings, plans, usage, and demo tools views."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import require_permission, require_tenant
from apps.accounts.permissions import can_manage_workspace
from apps.tenants.demo_reset import (
    reset_agent_runs,
    reset_conversations,
    reset_crm_data,
    reset_safe_demo_data,
    reset_webhook_events,
)
from apps.tenants.forms import DemoResetForm, PlanChangeForm, WorkspaceSettingsForm
from apps.tenants.models import Plan
from apps.tenants.plan_services import change_tenant_plan
from apps.tenants.usage import usage_with_limits


SETTINGS_CARDS = [
    {
        "title": "Workspace",
        "description": "Company profile, timezone, and currency",
        "url_name": "settings:workspace",
        "icon": "building",
    },
    {
        "title": "Team Members",
        "description": "Invite and manage workspace users",
        "url_name": "settings:team",
        "icon": "users",
    },
    {
        "title": "Roles & Permissions",
        "description": "Role capabilities reference",
        "url_name": "settings:roles",
        "icon": "shield",
    },
    {
        "title": "AI Providers",
        "description": "Mock and real AI provider configuration",
        "url_name": "agent_engine_settings:ai-providers",
        "icon": "cpu",
    },
    {
        "title": "Integrations",
        "description": "Channels, webhooks, and mock mode",
        "url_name": "integrations:index",
        "icon": "link",
    },
    {
        "title": "Plans & Usage",
        "description": "Current plan, limits, and usage metrics",
        "url_name": "settings:plan",
        "icon": "chart",
    },
    {
        "title": "Demo Tools",
        "description": "Reset demo data safely for presentations",
        "url_name": "settings:demo-tools",
        "icon": "refresh",
    },
    {
        "title": "Security",
        "description": "Encryption, rate limits, and production readiness",
        "url_name": "settings:security",
        "icon": "lock",
    },
    {
        "title": "Audit Logs",
        "description": "Security and workspace activity trail",
        "url_name": "settings:audit-logs",
        "icon": "list",
    },
]


@login_required
@require_tenant
def settings_home_view(request):
    return render(
        request,
        "settings/home.html",
        {
            "page_title": "Settings",
            "active_nav": "settings",
            "settings_cards": SETTINGS_CARDS,
        },
    )


@require_permission(can_manage_workspace)
def workspace_settings_view(request):
    tenant = request.tenant
    if request.method == "POST":
        form = WorkspaceSettingsForm(request.POST, instance=tenant)
        if form.is_valid():
            form.save()
            from apps.tenants.audit import log_audit_event

            log_audit_event(
                action="workspace_update",
                tenant=tenant,
                user=request.user,
                object_type="tenant",
                object_id=tenant.pk,
                metadata={"name": tenant.name},
                request=request,
            )
            messages.success(request, "Workspace settings updated.")
            return redirect("settings:workspace")
    else:
        form = WorkspaceSettingsForm(instance=tenant)

    return render(
        request,
        "settings/workspace.html",
        {
            "page_title": "Workspace Settings",
            "active_nav": "settings",
            "form": form,
        },
    )


@login_required
@require_tenant
def roles_permissions_view(request):
    from apps.accounts import permissions as perms

    role_matrix = [
        ("Owner", perms.is_owner, [
            "Full workspace control",
            "Manage team and plans",
            "All integrations and AI settings",
        ]),
        ("Admin", perms.is_admin, [
            "Manage workspace and team",
            "AI providers and integrations",
            "Analytics and knowledge",
        ]),
        ("Sales Manager", perms.is_manager, [
            "CRM, inbox, integrations",
            "Analytics and knowledge",
            "Human handoff",
        ]),
        ("Sales Rep", perms.is_sales_rep, [
            "CRM and inbox access",
            "Agent playground",
            "No settings or analytics",
        ]),
    ]
    return render(
        request,
        "settings/roles.html",
        {
            "page_title": "Roles & Permissions",
            "active_nav": "settings",
            "role_matrix": role_matrix,
            "current_role": request.user.role,
        },
    )


@require_permission(can_manage_workspace)
def plan_view(request):
    data = usage_with_limits(request.tenant)
    return render(
        request,
        "settings/plan.html",
        {
            "page_title": "Plans & Usage",
            "active_nav": "settings",
            **data,
        },
    )


@require_permission(can_manage_workspace)
def plan_change_view(request):
    tenant = request.tenant
    if request.method == "POST":
        form = PlanChangeForm(request.POST)
        if form.is_valid():
            change_tenant_plan(
                tenant,
                form.cleaned_data["plan"],
                user=request.user,
                request=request,
            )
            messages.success(request, f"Plan changed to {form.cleaned_data['plan'].name}.")
            return redirect("settings:plan")
    else:
        current = getattr(tenant, "subscription", None)
        initial_plan = current.plan if current else Plan.objects.filter(is_active=True).first()
        form = PlanChangeForm(initial={"plan": initial_plan})

    return render(
        request,
        "settings/plan_change.html",
        {
            "page_title": "Change Plan",
            "active_nav": "settings",
            "form": form,
            "plans": Plan.objects.filter(is_active=True),
        },
    )


@login_required
@require_tenant
def usage_dashboard_view(request):
    from apps.accounts.permissions import can_view_analytics

    if not can_view_analytics(request.user):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("You do not have permission to view usage.")

    data = usage_with_limits(request.tenant)
    return render(
        request,
        "settings/usage.html",
        {
            "page_title": "Usage Dashboard",
            "active_nav": "settings",
            **data,
        },
    )


@require_permission(can_manage_workspace)
def demo_tools_view(request):
    tenant = request.tenant
    results = None

    if request.method == "POST":
        form = DemoResetForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data["action"]
            if action == "conversations":
                results = {"conversations": reset_conversations(tenant)}
                messages.success(request, "Demo conversations reset.")
            elif action == "crm":
                results = {"crm": reset_crm_data(tenant)}
                messages.success(request, "Demo leads, tasks, and deals reset.")
            elif action == "agent_runs":
                results = {"agent_runs": reset_agent_runs(tenant)}
                messages.success(request, "Agent runs and tool calls reset.")
            elif action == "webhooks":
                results = {"webhooks": reset_webhook_events(tenant)}
                messages.success(request, "Webhook events reset.")
            elif action == "all_safe":
                results = reset_safe_demo_data(tenant, reseed=True)
                messages.success(request, "All demo data reset and re-seeded.")
            from apps.tenants.audit import log_audit_event

            log_audit_event(
                action="demo_reset",
                tenant=tenant,
                user=request.user,
                object_type="demo_reset",
                object_id=action,
                metadata={"action": action, "results": results or {}},
                request=request,
            )
            return redirect("settings:demo-tools")
    else:
        form = DemoResetForm()

    reset_actions = [
        ("conversations", "Reset demo conversations", "Clears all conversations and messages."),
        ("crm", "Reset demo leads/tasks/deals", "Clears CRM operational data."),
        ("agent_runs", "Reset agent runs/tool calls", "Clears agent run history and tool calls."),
        ("webhooks", "Reset webhook events", "Clears inbound webhook event log."),
        (
            "all_safe",
            "Reset all demo data and re-seed",
            "Clears conversations, CRM, runs, webhooks; re-seeds demo conversations and CRM.",
        ),
    ]

    return render(
        request,
        "settings/demo_tools.html",
        {
            "page_title": "Demo Tools",
            "active_nav": "settings",
            "form": form,
            "results": results,
            "reset_actions": reset_actions,
            "audit_command": "python scripts/audit_agent_quality.py",
        },
    )


@login_required
@require_tenant
def security_view(request):
    from apps.tenants.security_status import get_security_dashboard_context

    ctx = get_security_dashboard_context(request.user)
    return render(
        request,
        "settings/security.html",
        {
            "page_title": "Security",
            "active_nav": "settings",
            "user_email": request.user.email,
            **ctx,
        },
    )


@require_permission(can_manage_workspace)
def audit_logs_view(request):
    from apps.tenants.models import AuditLog

    qs = AuditLog.objects.filter(tenant=request.tenant).select_related("user")

    action_filter = request.GET.get("action", "").strip()
    if action_filter:
        qs = qs.filter(action=action_filter)

    user_filter = request.GET.get("user_id", "").strip()
    if user_filter.isdigit():
        qs = qs.filter(user_id=int(user_filter))

    date_from = request.GET.get("date_from", "").strip()
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)

    date_to = request.GET.get("date_to", "").strip()
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    logs = qs.order_by("-created_at")[:200]
    actions = (
        AuditLog.objects.filter(tenant=request.tenant)
        .values_list("action", flat=True)
        .distinct()
        .order_by("action")
    )
    from apps.accounts.models import User

    team_users = User.objects.filter(tenant=request.tenant).order_by("email")

    return render(
        request,
        "settings/audit_logs.html",
        {
            "page_title": "Audit Logs",
            "active_nav": "settings",
            "logs": logs,
            "actions": actions,
            "team_users": team_users,
            "filter_action": action_filter,
            "filter_user_id": user_filter,
            "filter_date_from": date_from,
            "filter_date_to": date_to,
        },
    )
