"""UAT and feedback permission helpers."""
from apps.accounts.models import User
from apps.accounts.permissions import is_admin, is_manager, is_owner, is_sales_rep


def can_manage_uat(user: User) -> bool:
    """Full UAT session management and sign-off."""
    return is_owner(user) or is_admin(user)


def can_participate_uat(user: User) -> bool:
    """View UAT dashboard, update checklist, view all feedback."""
    return is_owner(user) or is_admin(user) or is_manager(user)


def can_submit_feedback(user: User) -> bool:
    return bool(user and user.is_authenticated)


def can_edit_feedback(user: User, feedback) -> bool:
    if can_participate_uat(user):
        return True
    if is_sales_rep(user) and feedback.created_by_id == user.pk:
        return True
    return False
