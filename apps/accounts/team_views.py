"""Team management settings views."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import require_permission, require_tenant
from apps.accounts.forms import TeamInviteForm, TeamMemberEditForm
from apps.accounts.models import User
from apps.accounts.permissions import can_manage_team
from apps.accounts.team_services import TeamManagementError, create_team_member, update_team_member
from apps.tenants.plan_limits import check_team_member_limit


@require_permission(can_manage_team)
def team_list_view(request):
    members = User.objects.filter(tenant=request.tenant).order_by("-created_at")
    return render(
        request,
        "settings/team_list.html",
        {
            "page_title": "Team Members",
            "active_nav": "settings",
            "members": members,
        },
    )


@require_permission(can_manage_team)
def team_invite_view(request):
    tenant = request.tenant
    temp_password = None

    if request.method == "POST":
        form = TeamInviteForm(request.POST)
        if form.is_valid():
            limit = check_team_member_limit(tenant)
            if not limit.allowed:
                messages.warning(request, limit.message)
                return redirect("settings:team")

            try:
                user, temp_password = create_team_member(
                    tenant,
                    email=form.cleaned_data["email"],
                    full_name=form.cleaned_data["full_name"],
                    role=form.cleaned_data["role"],
                )
                if form.cleaned_data.get("send_invite_placeholder"):
                    messages.info(
                        request,
                        f"Invite placeholder: email would be sent to {user.email} "
                        f"(not sent in local demo).",
                    )
                messages.success(
                    request,
                    f"Team member {user.full_name} created. Temporary password: {temp_password}",
                )
                return redirect("settings:team")
            except TeamManagementError as exc:
                messages.error(request, str(exc))
    else:
        form = TeamInviteForm(initial={"role": "sales_rep"})

    return render(
        request,
        "settings/team_invite.html",
        {
            "page_title": "Invite Team Member",
            "active_nav": "settings",
            "form": form,
            "temp_password": temp_password,
        },
    )


@require_permission(can_manage_team)
def team_edit_view(request, user_id):
    member = get_object_or_404(User, pk=user_id, tenant=request.tenant)

    if request.method == "POST":
        form = TeamMemberEditForm(request.POST)
        if form.is_valid():
            try:
                update_team_member(
                    request.user,
                    member,
                    full_name=form.cleaned_data["full_name"],
                    role=form.cleaned_data["role"],
                    is_active=form.cleaned_data["is_active"],
                )
                messages.success(request, f"Updated {member.full_name}.")
                return redirect("settings:team")
            except TeamManagementError as exc:
                messages.error(request, str(exc))
    else:
        form = TeamMemberEditForm(
            initial={
                "full_name": member.full_name,
                "role": member.role,
                "is_active": member.is_active,
            }
        )

    return render(
        request,
        "settings/team_edit.html",
        {
            "page_title": f"Edit {member.full_name}",
            "active_nav": "settings",
            "form": form,
            "member": member,
        },
    )
