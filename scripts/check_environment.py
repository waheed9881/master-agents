#!/usr/bin/env python
"""
Environment validation for AI Agent OS.

Checks Python, Django, database, Redis, env vars, migrations, and static config.
ASCII-only output for Windows compatibility.

Usage:
    python scripts/check_environment.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

REQUIRED_ENV_VARS = [
    "SECRET_KEY",
    "DATABASE_URL",
    "REDIS_URL",
    "AI_PROVIDER",
    "META_VERIFY_TOKEN",
    "INTEGRATIONS_MOCK_MODE",
]

OPTIONAL_AI_VARS = ["OPENAI_API_KEY", "GROQ_API_KEY", "GEMINI_API_KEY"]
OPTIONAL_META_VARS = [
    "META_APP_SECRET",
    "META_ACCESS_TOKEN",
    "WHATSAPP_PHONE_NUMBER_ID",
    "INSTAGRAM_PAGE_ID",
]

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"

results: list[tuple[str, str, str]] = []


def record(status: str, check: str, detail: str) -> None:
    results.append((status, check, detail))
    print(f"[{status}] {check}: {detail}")


def check_python_version() -> None:
    major, minor = sys.version_info[:2]
    if major == 3 and minor >= 12:
        record(PASS, "Python version", f"{major}.{minor}")
    elif major == 3 and minor >= 10:
        record(WARN, "Python version", f"{major}.{minor} (3.12+ recommended)")
    else:
        record(FAIL, "Python version", f"{major}.{minor} (requires 3.10+)")


def check_django_settings() -> None:
    try:
        import django

        django.setup()
        from django.conf import settings

        record(PASS, "Django settings", f"loaded (DEBUG={settings.DEBUG})")
    except Exception as exc:
        record(FAIL, "Django settings", str(exc))


def check_database() -> None:
    try:
        from django.db import connection

        connection.ensure_connection()
        record(PASS, "Database connection", "ok")
    except Exception as exc:
        record(FAIL, "Database connection", str(exc))


def check_redis() -> None:
    try:
        from django.conf import settings

        import redis

        client = redis.from_url(settings.REDIS_URL, socket_connect_timeout=3)
        client.ping()
        record(PASS, "Redis connection", settings.REDIS_URL)
    except Exception as exc:
        record(WARN, "Redis connection", f"unavailable ({exc})")


def check_env_file() -> None:
    env_path = ROOT / ".env"
    if env_path.exists():
        record(PASS, ".env file", "found")
    else:
        record(WARN, ".env file", "not found (using defaults or shell env)")


def check_required_env_vars() -> None:
    from django.conf import settings

    missing = []
    for var in REQUIRED_ENV_VARS:
        if var == "SECRET_KEY":
            value = getattr(settings, "SECRET_KEY", "")
            if not value or value == "dev-insecure-key-change-in-production":
                missing.append(var)
            continue
        if not os.environ.get(var) and not hasattr(settings, var):
            missing.append(var)

    secret = getattr(settings, "SECRET_KEY", "")
    if secret and secret != "dev-insecure-key-change-in-production":
        record(PASS, "SECRET_KEY", "set")
    else:
        record(WARN, "SECRET_KEY", "using dev default (change for staging/production)")

    if missing:
        record(WARN, "Required env vars", f"missing or default: {', '.join(missing)}")
    else:
        record(PASS, "Required env vars", "present")


def check_ai_provider() -> None:
    from django.conf import settings

    provider = getattr(settings, "AI_PROVIDER", "mock")
    if provider == "mock":
        record(PASS, "AI provider", "mock (no API key required)")
        return

    key_map = {
        "openai": "OPENAI_API_KEY",
        "groq": "GROQ_API_KEY",
        "gemini": "GEMINI_API_KEY",
    }
    key_name = key_map.get(provider, "")
    key_value = getattr(settings, key_name, "") if key_name else ""
    if key_value:
        record(PASS, "AI provider", f"{provider} (API key set)")
    else:
        record(WARN, "AI provider", f"{provider} selected but {key_name} not set (will fallback to mock)")


def check_integrations_mock_mode() -> None:
    from django.conf import settings

    mock_mode = getattr(settings, "INTEGRATIONS_MOCK_MODE", True)
    if mock_mode:
        record(PASS, "Integrations mock mode", "enabled (safe for demo)")
    else:
        record(WARN, "Integrations mock mode", "disabled (live Meta credentials required)")


def check_migrations() -> None:
    try:
        from io import StringIO

        from django.core.management import call_command

        out = StringIO()
        call_command("showmigrations", "--plan", stdout=out, no_color=True)
        plan = out.getvalue()
        if "[ ]" in plan:
            record(WARN, "Migrations", "unapplied migrations detected (run migrate)")
        else:
            record(PASS, "Migrations", "all applied")
    except Exception as exc:
        record(WARN, "Migrations", f"could not check ({exc})")


def check_static_media() -> None:
    from django.conf import settings

    static_root = getattr(settings, "STATIC_ROOT", None)
    static_url = getattr(settings, "STATIC_URL", None)
    if static_root and static_url:
        record(PASS, "Static files config", f"STATIC_URL={static_url}")
    else:
        record(WARN, "Static files config", "STATIC_ROOT or STATIC_URL missing")


def main() -> int:
    print("AI Agent OS - Environment Check")
    print("=" * 40)

    check_python_version()
    check_env_file()
    check_django_settings()
    check_required_env_vars()
    check_database()
    check_redis()
    check_ai_provider()
    check_integrations_mock_mode()
    check_migrations()
    check_static_media()

    print("=" * 40)
    counts = {PASS: 0, WARN: 0, FAIL: 0}
    for status, _, _ in results:
        counts[status] = counts.get(status, 0) + 1

    print(f"Summary: {counts[PASS]} PASS, {counts[WARN]} WARN, {counts[FAIL]} FAIL")

    if counts[FAIL] > 0:
        print("Result: FAIL")
        return 1
    if counts[WARN] > 0:
        print("Result: WARN (review warnings before staging/production)")
        return 0
    print("Result: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
