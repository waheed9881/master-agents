"""UAT session and sign-off services."""
from django.utils import timezone

from apps.accounts.models import User
from apps.tenants.models import Tenant
from apps.uat.models import (
    ChecklistItemStatus,
    FeedbackPriority,
    FeedbackStatus,
    UATChecklistItem,
    UATSession,
    UATSessionStatus,
)
from apps.uat.selectors import critical_open_blockers


class UATSignOffError(Exception):
    pass


def create_session(
    tenant: Tenant,
    *,
    title: str,
    demo_version: str = "",
    audience: str = "",
    facilitator: str = "",
    created_by: User | None = None,
    copy_default_checklist: bool = True,
) -> UATSession:
    session = UATSession.objects.create(
        tenant=tenant,
        title=title,
        demo_version=demo_version,
        audience=audience,
        facilitator=facilitator,
        created_by=created_by,
        status=UATSessionStatus.DRAFT,
    )
    if copy_default_checklist:
        from apps.uat.default_checklist import DEFAULT_CHECKLIST_ITEMS

        for idx, item in enumerate(DEFAULT_CHECKLIST_ITEMS):
            UATChecklistItem.objects.create(
                tenant=tenant,
                session=session,
                section=item["section"],
                title=item["title"],
                description=item.get("description", ""),
                expected_result=item.get("expected_result", ""),
                order=idx,
            )
    return session


def mark_session_in_progress(session: UATSession) -> UATSession:
    if not session.started_at:
        session.started_at = timezone.now()
    session.status = UATSessionStatus.IN_PROGRESS
    session.save(update_fields=["status", "started_at", "updated_at"])
    return session


def mark_session_completed(session: UATSession) -> UATSession:
    session.status = UATSessionStatus.COMPLETED
    session.completed_at = timezone.now()
    session.save(update_fields=["status", "completed_at", "updated_at"])
    return session


def sign_off_session(session: UATSession, user: User) -> UATSession:
    blockers = critical_open_blockers(session.tenant)
    if blockers.exists():
        raise UATSignOffError(
            f"Cannot sign off: {blockers.count()} critical open blocker(s) remain."
        )
    session.status = UATSessionStatus.SIGNED_OFF
    session.signed_off_at = timezone.now()
    session.signed_off_by = user
    if not session.completed_at:
        session.completed_at = session.signed_off_at
    session.save(
        update_fields=["status", "signed_off_at", "signed_off_by", "completed_at", "updated_at"]
    )
    return session


def update_checklist_status(item: UATChecklistItem, status: str, notes: str = "") -> UATChecklistItem:
    item.status = status
    if notes:
        item.notes = notes
    item.save(update_fields=["status", "notes", "updated_at"])
    if item.session.status == UATSessionStatus.DRAFT:
        mark_session_in_progress(item.session)
    return item
