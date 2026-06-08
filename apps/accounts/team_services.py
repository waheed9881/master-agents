"""Team member management services."""
import secrets
import string

from django.db import transaction

from apps.accounts.models import User, UserRole
from apps.tenants.models import Tenant


class TeamManagementError(Exception):
    """Raised when a team operation is not allowed."""


def _active_owners(tenant: Tenant, exclude_user: User | None = None) -> int:
    qs = tenant.users.filter(role=UserRole.OWNER, is_active=True)
    if exclude_user:
        qs = qs.exclude(pk=exclude_user.pk)
    return qs.count()


def generate_temp_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#"
    return "".join(secrets.choice(alphabet) for _ in range(length))


@transaction.atomic
def create_team_member(
    tenant: Tenant,
    *,
    email: str,
    full_name: str,
    role: str,
    password: str | None = None,
    is_active: bool = True,
) -> tuple[User, str]:
    """Create a user in the tenant; returns user and password used."""
    if User.objects.filter(email=email).exists():
        raise TeamManagementError(f"A user with email {email} already exists.")
    temp_password = password or generate_temp_password()
    user = User.objects.create_user(
        email=email,
        password=temp_password,
        full_name=full_name,
        role=role,
        tenant=tenant,
        is_active=is_active,
    )
    from apps.tenants.audit import log_audit_event

    log_audit_event(
        action="team_member_create",
        tenant=tenant,
        user=None,
        object_type="user",
        object_id=user.pk,
        metadata={"email": email, "role": role},
    )
    return user, temp_password


@transaction.atomic
def update_team_member(
    actor: User,
    member: User,
    *,
    full_name: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
) -> User:
    """Update team member with owner-safety rules."""
    if member.tenant_id != actor.tenant_id:
        raise TeamManagementError("User is not in your workspace.")

    if is_active is False and member.pk == actor.pk:
        raise TeamManagementError("You cannot deactivate your own account.")

    if is_active is False and member.role == UserRole.OWNER:
        if _active_owners(member.tenant, exclude_user=member) == 0:
            raise TeamManagementError("At least one active owner must remain.")

    if role and role != UserRole.OWNER and member.role == UserRole.OWNER:
        if _active_owners(member.tenant, exclude_user=member) == 0:
            raise TeamManagementError("Cannot change role: at least one active owner required.")

    if full_name is not None:
        member.full_name = full_name
    if role is not None:
        member.role = role
    if is_active is not None:
        member.is_active = is_active
    member.save()

    action = "team_member_deactivate" if is_active is False else "team_member_update"
    from apps.tenants.audit import log_audit_event

    log_audit_event(
        action=action,
        tenant=member.tenant,
        user=actor,
        object_type="user",
        object_id=member.pk,
        metadata={
            "email": member.email,
            "role": member.role,
            "is_active": member.is_active,
        },
    )
    return member
