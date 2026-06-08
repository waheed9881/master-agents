"""UAT and feedback views."""
import csv
from io import StringIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import require_tenant
from apps.agent_engine.qa_status import PRODUCT_VERSION, SCENARIO_AUDIT_PASSED, SCENARIO_COUNT
from apps.uat.forms import ChecklistStatusForm, FeedbackItemForm, UATChecklistItemForm, UATSessionForm
from apps.uat.models import FeedbackItem, FeedbackStatus, UATChecklistItem, UATSession, UATSessionStatus
from apps.uat.permissions import can_edit_feedback, can_manage_uat, can_participate_uat, can_submit_feedback
from apps.uat import selectors
from apps.uat.services import (
    UATSignOffError,
    create_session,
    mark_session_completed,
    sign_off_session,
    update_checklist_status,
)


def _require_participate(request):
    if not can_participate_uat(request.user):
        return HttpResponseForbidden("You do not have permission to access UAT.")
    return None


@login_required
@require_tenant
def uat_dashboard_view(request):
    denied = _require_participate(request)
    if denied:
        return denied

    tenant = request.tenant
    counts = selectors.feedback_counts(tenant, request.user)
    sessions = selectors.active_sessions(tenant)[:5]
    recent_feedback = selectors.feedback_for_user(tenant, request.user)[:8]
    signed_off = selectors.sessions_for_tenant(tenant).filter(status=UATSessionStatus.SIGNED_OFF).first()

    return render(
        request,
        "uat/dashboard.html",
        {
            "page_title": "UAT and Feedback",
            "active_nav": "uat",
            "feedback_counts": counts,
            "active_sessions": sessions,
            "recent_feedback": recent_feedback,
            "signed_off_session": signed_off,
            "critical_blockers": selectors.critical_open_blockers(tenant)[:5],
        },
    )


@login_required
@require_tenant
def session_list_view(request):
    denied = _require_participate(request)
    if denied:
        return denied
    sessions = selectors.sessions_for_tenant(request.tenant)
    return render(
        request,
        "uat/session_list.html",
        {
            "page_title": "UAT Sessions",
            "active_nav": "uat",
            "sessions": sessions,
        },
    )


@login_required
@require_tenant
def session_create_view(request):
    if not can_manage_uat(request.user):
        return HttpResponseForbidden("Only owners and admins can create UAT sessions.")

    if request.method == "POST":
        form = UATSessionForm(request.POST)
        if form.is_valid():
            session = create_session(
                request.tenant,
                title=form.cleaned_data["title"],
                demo_version=form.cleaned_data.get("demo_version") or PRODUCT_VERSION,
                audience=form.cleaned_data.get("audience", ""),
                facilitator=form.cleaned_data.get("facilitator", ""),
                created_by=request.user,
            )
            if form.cleaned_data.get("summary"):
                session.summary = form.cleaned_data["summary"]
                session.save(update_fields=["summary", "updated_at"])
            messages.success(request, f"UAT session '{session.title}' created with default checklist.")
            return redirect("uat:session-detail", session_id=session.pk)
    else:
        form = UATSessionForm(initial={"demo_version": PRODUCT_VERSION})

    return render(
        request,
        "uat/session_form.html",
        {"page_title": "New UAT Session", "active_nav": "uat", "form": form},
    )


@login_required
@require_tenant
def session_detail_view(request, session_id):
    denied = _require_participate(request)
    if denied:
        return denied

    session = get_object_or_404(UATSession, pk=session_id, tenant=request.tenant)
    progress = selectors.session_progress(session)
    sections = selectors.checklist_by_section(session)
    feedback = session.feedback_items.select_related("created_by").order_by("-created_at")[:20]
    checklist_form = ChecklistStatusForm()

    if request.method == "POST":
        action = request.POST.get("action")
        if action in ("complete", "sign_off") and can_manage_uat(request.user):
            if action == "complete":
                mark_session_completed(session)
                messages.success(request, "Session marked completed.")
            elif action == "sign_off":
                try:
                    sign_off_session(session, request.user)
                    messages.success(request, "Session signed off successfully.")
                except UATSignOffError as exc:
                    messages.error(request, str(exc))
            return redirect("uat:session-detail", session_id=session.pk)
        if action == "update_checklist" and can_participate_uat(request.user):
            form = ChecklistStatusForm(request.POST)
            if form.is_valid():
                item = get_object_or_404(
                    UATChecklistItem,
                    pk=form.cleaned_data["item_id"],
                    session=session,
                    tenant=request.tenant,
                )
                update_checklist_status(
                    item,
                    form.cleaned_data["status"],
                    form.cleaned_data.get("notes", ""),
                )
                messages.success(request, f"Updated: {item.title}")
            return redirect("uat:session-detail", session_id=session.pk)

    critical_count = selectors.critical_open_blockers(request.tenant).count()

    return render(
        request,
        "uat/session_detail.html",
        {
            "page_title": session.title,
            "active_nav": "uat",
            "session": session,
            "progress": progress,
            "sections": sections,
            "feedback": feedback,
            "checklist_form": checklist_form,
            "can_manage": can_manage_uat(request.user),
            "can_update_checklist": can_participate_uat(request.user),
            "critical_blocker_count": critical_count,
        },
    )


@login_required
@require_tenant
def checklist_add_view(request, session_id):
    if not can_manage_uat(request.user):
        return HttpResponseForbidden("Only owners and admins can add checklist items.")

    session = get_object_or_404(UATSession, pk=session_id, tenant=request.tenant)
    if request.method == "POST":
        form = UATChecklistItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.tenant = request.tenant
            item.session = session
            item.save()
            messages.success(request, "Checklist item added.")
            return redirect("uat:session-detail", session_id=session.pk)
    else:
        form = UATChecklistItemForm(initial={"order": session.checklist_items.count()})

    return render(
        request,
        "uat/checklist_form.html",
        {"page_title": "Add Checklist Item", "active_nav": "uat", "form": form, "session": session},
    )


@login_required
@require_tenant
def feedback_list_view(request):
    if not can_submit_feedback(request.user):
        return HttpResponseForbidden("Permission denied.")

    qs = selectors.feedback_for_user(request.tenant, request.user)

    category = request.GET.get("category", "")
    priority = request.GET.get("priority", "")
    status = request.GET.get("status", "")
    module = request.GET.get("module", "")

    if category:
        qs = qs.filter(category=category)
    if priority:
        qs = qs.filter(priority=priority)
    if status:
        qs = qs.filter(status=status)
    if module:
        qs = qs.filter(module_area=module)

    if request.method == "POST" and can_participate_uat(request.user):
        item_id = request.POST.get("item_id")
        new_status = request.POST.get("status")
        if item_id and new_status:
            item = get_object_or_404(FeedbackItem, pk=item_id, tenant=request.tenant)
            item.status = new_status
            item.save(update_fields=["status", "updated_at"])
            messages.success(request, "Feedback status updated.")
            return redirect("uat:feedback-list")

    return render(
        request,
        "uat/feedback_list.html",
        {
            "page_title": "Feedback",
            "active_nav": "uat",
            "feedback_items": qs[:200],
            "filter_category": category,
            "filter_priority": priority,
            "filter_status": status,
            "filter_module": module,
            "can_triage": can_participate_uat(request.user),
        },
    )


@login_required
@require_tenant
def feedback_create_view(request):
    if not can_submit_feedback(request.user):
        return HttpResponseForbidden("Permission denied.")

    initial = {
        "module_area": request.GET.get("module", ""),
        "related_url": request.GET.get("url", ""),
    }
    session_id = request.GET.get("session")
    if session_id:
        initial["session"] = session_id

    if request.method == "POST":
        form = FeedbackItemForm(request.POST, tenant=request.tenant, user=request.user)
        if form.is_valid():
            item = form.save(commit=False)
            item.tenant = request.tenant
            item.created_by = request.user
            if not can_participate_uat(request.user):
                item.status = FeedbackStatus.OPEN
            item.save()
            messages.success(request, "Feedback submitted.")
            return redirect("uat:feedback-list")
    else:
        form = FeedbackItemForm(initial=initial, tenant=request.tenant, user=request.user)

    return render(
        request,
        "uat/feedback_form.html",
        {"page_title": "Report Feedback", "active_nav": "uat", "form": form, "is_create": True},
    )


@login_required
@require_tenant
def feedback_edit_view(request, item_id):
    item = get_object_or_404(FeedbackItem, pk=item_id, tenant=request.tenant)
    if not can_edit_feedback(request.user, item):
        return HttpResponseForbidden("You cannot edit this feedback item.")

    if request.method == "POST":
        form = FeedbackItemForm(request.POST, instance=item, tenant=request.tenant, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Feedback updated.")
            return redirect("uat:feedback-list")
    else:
        form = FeedbackItemForm(instance=item, tenant=request.tenant, user=request.user)

    return render(
        request,
        "uat/feedback_form.html",
        {"page_title": "Edit Feedback", "active_nav": "uat", "form": form, "is_create": False},
    )


@login_required
@require_tenant
def feedback_export_csv_view(request):
    if not can_participate_uat(request.user):
        return HttpResponseForbidden("Permission denied.")

    qs = selectors.feedback_for_user(request.tenant, request.user)
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "title", "category", "priority", "status", "module_area",
        "created_at", "assigned_to", "description",
    ])
    for item in qs:
        writer.writerow([
            item.title,
            item.category,
            item.priority,
            item.status,
            item.module_area,
            item.created_at.isoformat() if item.created_at else "",
            item.assigned_to.email if item.assigned_to else "",
            item.description.replace("\n", " ").replace("\r", ""),
        ])

    response = HttpResponse(buffer.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="uat_feedback_export.csv"'
    return response


@login_required
@require_tenant
def uat_report_view(request):
    denied = _require_participate(request)
    if denied:
        return denied

    tenant = request.tenant
    sessions = selectors.sessions_for_tenant(tenant)
    all_feedback = selectors.feedback_for_user(tenant, request.user)
    blockers = selectors.critical_open_blockers(tenant)
    signed_off = sessions.filter(status=UATSessionStatus.SIGNED_OFF)

    session_summaries = []
    for session in sessions[:10]:
        session_summaries.append({
            "session": session,
            "progress": selectors.session_progress(session),
        })

    return render(
        request,
        "uat/report.html",
        {
            "page_title": "UAT Sign-off Report",
            "active_nav": "uat",
            "sessions": session_summaries,
            "signed_off_count": signed_off.count(),
            "open_blockers": blockers,
            "feedback_open": all_feedback.filter(status=FeedbackStatus.OPEN).count(),
            "scenario_audit": f"{SCENARIO_AUDIT_PASSED}/{SCENARIO_COUNT}",
            "product_version": PRODUCT_VERSION,
        },
    )
