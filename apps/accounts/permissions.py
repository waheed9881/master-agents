"""Role-based permission helpers for tenant-scoped access control."""
from apps.accounts.models import User, UserRole


def is_owner(user: User) -> bool:
    return bool(user and user.is_authenticated and user.role == UserRole.OWNER)


def is_admin(user: User) -> bool:
    return bool(user and user.is_authenticated and user.role == UserRole.ADMIN)


def is_manager(user: User) -> bool:
    return bool(
        user
        and user.is_authenticated
        and user.role == UserRole.SALES_MANAGER
    )


def is_sales_rep(user: User) -> bool:
    return bool(
        user
        and user.is_authenticated
        and user.role == UserRole.SALES_REP
    )


def can_manage_workspace(user: User) -> bool:
    return is_owner(user) or is_admin(user)


def can_manage_team(user: User) -> bool:
    return is_owner(user) or is_admin(user)


def can_manage_integrations(user: User) -> bool:
    return is_owner(user) or is_admin(user) or is_manager(user)


def can_manage_ai_providers(user: User) -> bool:
    return is_owner(user) or is_admin(user)


def can_manage_knowledge(user: User) -> bool:
    return not is_sales_rep(user)


def can_view_analytics(user: User) -> bool:
    return not is_sales_rep(user)


def can_use_agent_playground(user: User) -> bool:
    return bool(user and user.is_authenticated)


def can_take_human_handoff(user: User) -> bool:
    return bool(user and user.is_authenticated and not is_sales_rep(user))
