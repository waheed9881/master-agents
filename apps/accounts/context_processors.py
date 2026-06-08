"""Template context for tenant and navigation."""
from django.conf import settings

DEMO_EMAIL = "admin@example.com"


def tenant_context(request):
    tenant = getattr(request, "tenant", None)
    return {
        "current_tenant": tenant,
    }


def demo_env_context(request):
    """Global local-demo flags for banners and topbar badges."""
    mock_ai = getattr(settings, "AI_PROVIDER", "mock") == "mock"
    integrations_mock = getattr(settings, "INTEGRATIONS_MOCK_MODE", True)
    user = getattr(request, "user", None)
    is_demo_user = bool(user and user.is_authenticated and user.email == DEMO_EMAIL)

    parts = []
    if mock_ai:
        parts.append("AI uses mock provider")
    if integrations_mock:
        parts.append("integrations in mock mode")
    if settings.DEBUG:
        parts.append("DEBUG=True")

    show_banner = mock_ai or integrations_mock or settings.DEBUG or is_demo_user
    banner_tone = "warning" if is_demo_user else "info"
    if is_demo_user:
        message = (
            "Change the demo password before external presentations. "
            + ("; ".join(parts) if parts else "Local demo environment.")
        )
    elif parts:
        message = "; ".join(parts) + ". Safe for local client demos."
    else:
        message = "Local demo environment."

    return {
        "demo_env": {
            "show_banner": show_banner,
            "banner_tone": banner_tone,
            "banner_message": message,
            "mock_ai": mock_ai,
            "integrations_mock": integrations_mock,
            "is_demo_user": is_demo_user,
            "debug_mode": settings.DEBUG,
        }
    }
