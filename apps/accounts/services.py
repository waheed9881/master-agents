"""Authentication services."""
from django.contrib.auth import authenticate

from apps.accounts.models import User


def authenticate_user(email: str, password: str) -> User | None:
    """Authenticate user by email and password."""
    user = authenticate(username=email, password=password)
    if user and user.is_active:
        return user
    return None
