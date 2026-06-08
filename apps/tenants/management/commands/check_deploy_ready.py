"""Deployment readiness check for staging and production."""
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.accounts.models import User

INSECURE_SECRET_KEYS = {
    "dev-insecure-key-change-in-production",
    "change-me-in-production-use-a-long-random-string",
}
LOCAL_ONLY_HOSTS = {"localhost", "127.0.0.1", "web", "testserver"}
DEMO_EMAIL = "admin@example.com"


class Command(BaseCommand):
    help = "Check deployment readiness for staging/production"

    def handle(self, *args, **options):
        self.stdout.write("AI Agent OS - Deployment Readiness Check")
        self.stdout.write("=" * 45)

        warnings = 0
        failures = 0

        if settings.DEBUG:
            self._line("WARN", "DEBUG", "True (must be False in production)")
            warnings += 1
        else:
            self._line("PASS", "DEBUG", "False")

        hosts = settings.ALLOWED_HOSTS
        host_set = set(hosts or [])
        if not settings.DEBUG and (not host_set or host_set.issubset(LOCAL_ONLY_HOSTS)):
            self._line("WARN", "ALLOWED_HOSTS", f"{hosts} (must include staging/production domain)")
            warnings += 1
        elif hosts:
            self._line("PASS", "ALLOWED_HOSTS", ", ".join(hosts))
        else:
            self._line("WARN", "ALLOWED_HOSTS", "empty")
            warnings += 1

        secret = settings.SECRET_KEY
        if not secret or secret in INSECURE_SECRET_KEYS:
            self._line("FAIL", "SECRET_KEY", "insecure or default value")
            failures += 1
        elif len(secret) < 32:
            self._line("WARN", "SECRET_KEY", "set but shorter than 32 chars")
            warnings += 1
        else:
            self._line("PASS", "SECRET_KEY", "set")

        db = settings.DATABASES.get("default", {})
        db_name = db.get("NAME", "")
        db_host = db.get("HOST", "")
        self._line("PASS", "Database", f"{db_name} @ {db_host or 'default'}")

        redis_url = getattr(settings, "REDIS_URL", "")
        if redis_url:
            self._line("PASS", "Redis URL", redis_url)
        else:
            self._line("WARN", "Redis URL", "not configured")
            warnings += 1

        provider = getattr(settings, "AI_PROVIDER", "mock")
        if provider == "mock":
            self._line("PASS", "AI provider", "mock (demo-safe)")
        else:
            key_map = {
                "openai": ("OPENAI_API_KEY", settings.OPENAI_API_KEY),
                "groq": ("GROQ_API_KEY", settings.GROQ_API_KEY),
                "gemini": ("GEMINI_API_KEY", settings.GEMINI_API_KEY),
            }
            key_name, key_val = key_map.get(provider, ("", ""))
            if key_val:
                self._line("PASS", "AI provider", f"{provider} ({key_name} set)")
            else:
                self._line("WARN", "AI provider", f"{provider} but {key_name} missing")
                warnings += 1

        mock_mode = getattr(settings, "INTEGRATIONS_MOCK_MODE", True)
        if mock_mode:
            self._line("PASS", "Meta mock mode", "enabled")
        else:
            self._line("WARN", "Meta mock mode", "disabled (live Meta setup required)")
            warnings += 1
            missing_meta = []
            if not getattr(settings, "META_APP_SECRET", ""):
                missing_meta.append("META_APP_SECRET")
            if not getattr(settings, "META_ACCESS_TOKEN", ""):
                missing_meta.append("META_ACCESS_TOKEN")
            if not getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "") and not getattr(
                settings, "INSTAGRAM_PAGE_ID", ""
            ):
                missing_meta.append("WHATSAPP_PHONE_NUMBER_ID or INSTAGRAM_PAGE_ID")
            if missing_meta:
                self._line("WARN", "Meta credentials", f"missing: {', '.join(missing_meta)}")
                warnings += 1

        csrf_origins = getattr(settings, "CSRF_TRUSTED_ORIGINS", [])
        if not settings.DEBUG and not csrf_origins:
            self._line("WARN", "CSRF_TRUSTED_ORIGINS", "empty (set for HTTPS domain)")
            warnings += 1
        elif csrf_origins:
            self._line("PASS", "CSRF_TRUSTED_ORIGINS", ", ".join(csrf_origins))
        else:
            self._line("PASS", "CSRF_TRUSTED_ORIGINS", "not required in DEBUG mode")

        if User.objects.filter(email=DEMO_EMAIL).exists():
            self._line(
                "WARN",
                "Demo account",
                f"{DEMO_EMAIL} exists - change password before production",
            )
            warnings += 1
        else:
            self._line("PASS", "Demo account", "not found")

        self.stdout.write("=" * 45)
        if failures:
            self.stdout.write(self.style.ERROR(f"Result: FAIL ({failures} failure(s), {warnings} warning(s))"))
        elif warnings:
            self.stdout.write(self.style.WARNING(f"Result: WARN ({warnings} warning(s))"))
        else:
            self.stdout.write(self.style.SUCCESS("Result: PASS"))

    def _line(self, status: str, check: str, detail: str):
        self.stdout.write(f"[{status}] {check}: {detail}")
