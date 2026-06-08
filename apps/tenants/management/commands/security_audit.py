"""Comprehensive local security audit command."""
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection

from apps.accounts.models import User
from apps.integrations.services.credential_encryption import encryption_status
from apps.tenants.security_status import (
    DEMO_EMAIL,
    INSECURE_SECRET_KEYS,
    LOCAL_ONLY_HOSTS,
    _allowed_hosts_status,
    _csrf_status,
    _debug_status,
    _demo_account_status,
    _rate_limit_status,
    _secret_key_status,
)

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"


class Command(BaseCommand):
    help = "Run local security audit (no external APIs required)"

    def handle(self, *args, **options):
        self.stdout.write("AI Agent OS - Security Audit")
        self.stdout.write("=" * 45)

        warnings = 0
        failures = 0

        for check, result in self._run_checks():
            status = result["status"]
            self.stdout.write(f"[{status}] {check}: {result['message']}")
            if status == WARN:
                warnings += 1
            elif status == FAIL:
                failures += 1

        self.stdout.write("=" * 45)
        if failures:
            self.stdout.write(
                self.style.ERROR(f"Result: FAIL ({failures} failure(s), {warnings} warning(s))")
            )
        elif warnings:
            self.stdout.write(self.style.WARNING(f"Result: WARN ({warnings} warning(s))"))
        else:
            self.stdout.write(self.style.SUCCESS("Result: PASS"))

    def _run_checks(self):
        yield "DEBUG", _debug_status()
        yield "SECRET_KEY", _secret_key_status()
        yield "ALLOWED_HOSTS", _allowed_hosts_status()
        yield "CSRF_TRUSTED_ORIGINS", _csrf_status()
        yield "CREDENTIALS_ENCRYPTION_KEY", encryption_status()

        mock_mode = getattr(settings, "INTEGRATIONS_MOCK_MODE", True)
        if mock_mode:
            yield "INTEGRATIONS_MOCK_MODE", {"status": PASS, "message": "enabled (demo-safe)"}
        else:
            yield "INTEGRATIONS_MOCK_MODE", {
                "status": WARN,
                "message": "disabled (live Meta required)",
            }

        provider = getattr(settings, "AI_PROVIDER", "mock")
        if provider == "mock":
            yield "AI_PROVIDER", {"status": PASS, "message": "mock (no API key required)"}
        else:
            key_map = {
                "openai": settings.OPENAI_API_KEY,
                "groq": settings.GROQ_API_KEY,
                "gemini": settings.GEMINI_API_KEY,
            }
            key_val = key_map.get(provider, "")
            if key_val:
                yield "AI_PROVIDER", {"status": PASS, "message": f"{provider} (API key set)"}
            else:
                yield "AI_PROVIDER", {
                    "status": WARN,
                    "message": f"{provider} selected but API key missing",
                }

        yield "Demo account", _demo_account_status()
        yield "Rate limiting", _rate_limit_status()

        try:
            connection.ensure_connection()
            db = settings.DATABASES.get("default", {})
            yield "Database", {
                "status": PASS,
                "message": f"{db.get('NAME', '')} connected",
            }
        except Exception as exc:
            yield "Database", {"status": FAIL, "message": str(exc)}

        try:
            from apps.tenants.models import AuditLog

            count = AuditLog.objects.count()
            yield "Audit log table", {"status": PASS, "message": f"exists ({count} entries)"}
        except Exception as exc:
            yield "Audit log table", {"status": FAIL, "message": str(exc)}

        backups_dir = getattr(settings, "BACKUPS_DIR", None)
        if backups_dir and backups_dir.exists():
            files = list(backups_dir.glob("*"))
            yield "Backups folder", {
                "status": PASS,
                "message": f"{backups_dir} ({len(files)} file(s))",
            }
        elif backups_dir:
            yield "Backups folder", {
                "status": WARN,
                "message": f"{backups_dir} does not exist yet (run local_backup.py)",
            }
        else:
            yield "Backups folder", {"status": WARN, "message": "BACKUPS_DIR not configured"}

        secret = settings.SECRET_KEY
        if secret in INSECURE_SECRET_KEYS:
            pass  # already covered
        elif not secret:
            yield "SECRET_KEY presence", {"status": FAIL, "message": "missing"}

        if not settings.DEBUG and not getattr(settings, "CREDENTIALS_ENCRYPTION_KEY", ""):
            enc = encryption_status()
            if enc["status"] == FAIL:
                yield "Production encryption", enc
