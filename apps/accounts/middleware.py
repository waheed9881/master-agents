"""Attach current tenant to request from authenticated user."""
from django.utils.functional import SimpleLazyObject


def _get_tenant(request):
    user = getattr(request, "user", None)
    if user and user.is_authenticated and hasattr(user, "tenant"):
        return user.tenant
    return None


class TenantMiddleware:
    """Expose request.tenant for downstream views and services."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tenant = SimpleLazyObject(lambda: _get_tenant(request))
        return self.get_response(request)
