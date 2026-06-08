"""Security status helpers for dashboard and audit commands."""
from __future__ import annotations

from django.conf import settings

from apps.accounts.models import User
from apps.integrations.services.credential_encryption import encryption_status

INSECURE_SECRET_KEYS = {
    "dev-insecure-key-change-in-production",
    "change-me-in-production-use-a-long-random-string",
}
LOCAL_ONLY_HOSTS = {"localhost", "127.0.0.1", "web", "testserver"}
DEMO_EMAIL = "admin@example.com"


def _secret_key_status() -> dict:
    secret = settings.SECRET_KEY
    if not secret or secret in INSECURE_SECRET_KEYS:
        return {"status": "FAIL", "message": "Default or insecure SECRET_KEY"}
    if len(secret) < 32:
        return {"status": "WARN", "message": f"SECRET_KEY is only {len(secret)} chars"}
    return {"status": "PASS", "message": "SECRET_KEY is set and strong"}


def _allowed_hosts_status() -> dict:
    hosts = list(settings.ALLOWED_HOSTS or [])
    host_set = set(hosts)
    if not settings.DEBUG and (not host_set or host_set.issubset(LOCAL_ONLY_HOSTS)):
        return {"status": "WARN", "message": f"ALLOWED_HOSTS: {hosts} (add production domain)"}
    if hosts:
        return {"status": "PASS", "message": ", ".join(hosts)}
    return {"status": "WARN", "message": "ALLOWED_HOSTS is empty"}


def _csrf_status() -> dict:
    origins = list(getattr(settings, "CSRF_TRUSTED_ORIGINS", []) or [])
    if not settings.DEBUG and not origins:
        return {"status": "WARN", "message": "CSRF_TRUSTED_ORIGINS empty (required for HTTPS)"}
    if origins:
        return {"status": "PASS", "message": ", ".join(origins)}
    return {"status": "PASS", "message": "Not required in DEBUG mode"}


def _demo_account_status() -> dict:
    if User.objects.filter(email=DEMO_EMAIL).exists():
        return {
            "status": "WARN",
            "message": f"{DEMO_EMAIL} exists - change password before external demo",
        }
    return {"status": "PASS", "message": "Demo account not found"}


def _rate_limit_status() -> dict:
    enabled = getattr(settings, "RATE_LIMITING_ENABLED", True)
    if enabled:
        return {
            "status": "PASS",
            "message": (
                f"Enabled (webchat={settings.RATE_LIMIT_WEBCHAT_PER_MINUTE}/min, "
                f"webhook={settings.RATE_LIMIT_WEBHOOK_PER_MINUTE}/min)"
            ),
        }
    return {"status": "WARN", "message": "Rate limiting disabled"}


def get_security_dashboard_context(user) -> dict:
    """Build context for /settings/security/ dashboard."""
    enc = encryption_status()
    mock_mode = getattr(settings, "INTEGRATIONS_MOCK_MODE", True)
    provider = getattr(settings, "AI_PROVIDER", "mock")

    cards = [
        {"title": "DEBUG", **_debug_status()},
        {"title": "Secret Key", **_secret_key_status()},
        {"title": "Allowed Hosts", **_allowed_hosts_status()},
        {"title": "CSRF Trusted Origins", **_csrf_status()},
        {"title": "Credential Encryption", **enc},
        {"title": "Mock Mode", **_mock_mode_status(mock_mode)},
        {"title": "Rate Limiting", **_rate_limit_status()},
        {"title": "Demo Account", **_demo_account_status()},
    ]

    blockers = []
    for card in cards:
        if card.get("status") == "FAIL":
            blockers.append(f"{card['title']}: {card['message']}")
    if not getattr(settings, "CREDENTIALS_ENCRYPTION_KEY", "") and not mock_mode:
        blockers.append("CREDENTIALS_ENCRYPTION_KEY required for live integrations")
    if settings.DEBUG:
        blockers.append("DEBUG must be False for production")
    if User.objects.filter(email=DEMO_EMAIL).exists():
        blockers.append(f"Change password for {DEMO_EMAIL}")

    from apps.tenants.models import AuditLog

    recent_logs = []
    if user and user.tenant_id:
        recent_logs = list(
            AuditLog.objects.filter(tenant=user.tenant)
            .select_related("user")
            .order_by("-created_at")[:10]
        )

    is_demo_user = user.email == DEMO_EMAIL if user else False

    return {
        "security_cards": cards,
        "production_blockers": blockers,
        "recent_audit_logs": recent_logs,
        "encryption_status": enc,
        "mock_mode": mock_mode,
        "ai_provider": provider,
        "is_demo_user": is_demo_user,
        "demo_email": DEMO_EMAIL,
        "rate_limiting_enabled": getattr(settings, "RATE_LIMITING_ENABLED", True),
    }


def _debug_status() -> dict:
    if settings.DEBUG:
        return {"status": "WARN", "message": "DEBUG=True (disable for production)"}
    return {"status": "PASS", "message": "DEBUG=False"}


def _mock_mode_status(mock_mode: bool) -> dict:
    if mock_mode:
        return {"status": "PASS", "message": "INTEGRATIONS_MOCK_MODE enabled (demo-safe)"}
    return {"status": "WARN", "message": "Live integrations mode - Meta credentials required"}
