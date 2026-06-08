"""UAT query helpers."""
from django.db.models import Count, Q, QuerySet

from apps.tenants.models import Tenant
from apps.uat.models import (
    ChecklistItemStatus,
    FeedbackItem,
    FeedbackPriority,
    FeedbackStatus,
    UATChecklistItem,
    UATSession,
    UATSessionStatus,
)


def sessions_for_tenant(tenant: Tenant) -> QuerySet[UATSession]:
    return UATSession.objects.filter(tenant=tenant).select_related("created_by", "signed_off_by")


def active_sessions(tenant: Tenant) -> QuerySet[UATSession]:
    return sessions_for_tenant(tenant).filter(
        status__in=[UATSessionStatus.DRAFT, UATSessionStatus.IN_PROGRESS]
    )


def feedback_for_user(tenant: Tenant, user) -> QuerySet[FeedbackItem]:
    from apps.accounts.permissions import is_sales_rep
    from apps.uat.permissions import can_participate_uat

    qs = FeedbackItem.objects.filter(tenant=tenant).select_related(
        "created_by", "assigned_to", "session"
    )
    if can_participate_uat(user):
        return qs
    if is_sales_rep(user):
        return qs.filter(created_by=user)
    return qs.none()


def feedback_counts(tenant: Tenant, user=None) -> dict:
    qs = FeedbackItem.objects.filter(tenant=tenant)
    if user:
        from apps.accounts.permissions import is_sales_rep
        from apps.uat.permissions import can_participate_uat

        if is_sales_rep(user) and not can_participate_uat(user):
            qs = qs.filter(created_by=user)
    return {
        "total": qs.count(),
        "open": qs.filter(status=FeedbackStatus.OPEN).count(),
        "critical": qs.filter(
            priority=FeedbackPriority.CRITICAL,
            status__in=[FeedbackStatus.OPEN, FeedbackStatus.TRIAGED, FeedbackStatus.IN_PROGRESS],
        ).count(),
        "high": qs.filter(
            priority=FeedbackPriority.HIGH,
            status__in=[FeedbackStatus.OPEN, FeedbackStatus.TRIAGED, FeedbackStatus.IN_PROGRESS],
        ).count(),
    }


def critical_open_blockers(tenant: Tenant) -> QuerySet[FeedbackItem]:
    return FeedbackItem.objects.filter(
        tenant=tenant,
        priority=FeedbackPriority.CRITICAL,
        status__in=[FeedbackStatus.OPEN, FeedbackStatus.TRIAGED, FeedbackStatus.IN_PROGRESS],
    )


def session_progress(session: UATSession) -> dict:
    items = session.checklist_items.all()
    total = items.count()
    if not total:
        return {"total": 0, "passed": 0, "failed": 0, "blocked": 0, "percent": 0}
    passed = items.filter(status=ChecklistItemStatus.PASSED).count()
    failed = items.filter(status=ChecklistItemStatus.FAILED).count()
    blocked = items.filter(status=ChecklistItemStatus.BLOCKED).count()
    tested = items.exclude(status=ChecklistItemStatus.NOT_TESTED).count()
    percent = round((tested / total) * 100, 1)
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "blocked": blocked,
        "percent": percent,
    }


def checklist_by_section(session: UATSession) -> list[dict]:
    sections = {}
    for item in session.checklist_items.all():
        sections.setdefault(item.section, []).append(item)
    return [{"section": k, "items": v} for k, v in sections.items()]
