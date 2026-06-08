"""View decorators for permission checks."""
from functools import wraps
from typing import Callable

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseForbidden

from apps.accounts.models import User


def require_tenant(view_func):
    """Ensure request has a tenant; raise 404 otherwise."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.tenant:
            raise Http404("No tenant")
        return view_func(request, *args, **kwargs)

    return _wrapped


def require_permission(check_fn: Callable[[User], bool], message: str = "Permission denied."):
    """Decorator requiring a permission helper to return True for the user."""

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        @require_tenant
        def _wrapped(request, *args, **kwargs):
            if not check_fn(request.user):
                return HttpResponseForbidden(message)
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
