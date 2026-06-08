# Security

## Current Security Basics

| Control | Status |
|---------|--------|
| Django session auth | Implemented |
| CSRF protection | Enabled (staff UI and session API) |
| Tenant middleware scoping | Implemented |
| Role-based access (owner/admin/manager/rep) | Implemented (Phase 15) |
| Settings/team restricted to owner/admin | Implemented |
| Sales rep blocked from analytics/settings/audit logs | Implemented |
| Password validators | Django defaults |
| Password change UI | `/settings/security/password/` |
| Fernet credential encryption | Implemented (Phase 16) |
| Local rate limiting | Implemented (Phase 16, cache-based) |
| Security audit log | Implemented (Phase 16) |
| Security dashboard | `/settings/security/` |
| Webhook CSRF exempt | Only on webhook endpoints |
| X-Frame-Options | DENY in production |
| Secure cookies | Enabled when DEBUG=False |

## Credential Encryption (Phase 16)

Channel integration tokens (`access_token`, `app_secret`) are encrypted with Fernet when `CREDENTIALS_ENCRYPTION_KEY` is set.

Generate a key:

```bash
python manage.py generate_credentials_key
```

Add the output to `.env`:

```
CREDENTIALS_ENCRYPTION_KEY=<fernet-key>
```

Behavior:

- **Key set:** new credentials encrypted; existing `plain:` values work and can be re-saved to encrypt
- **Key missing + mock mode:** credentials stored as `plain:` prefix (local dev warning)
- **Key missing + live mode:** deploy readiness FAIL

Secrets are **never** shown in UI or API — only masked values (`****abcd (encrypted)`).

Helper module: `apps/integrations/services/credential_encryption.py`

## Rate Limiting (Phase 16)

Local cache-based rate limiting (no paid external service). Falls back to in-memory counters if Redis/cache unavailable.

| Env var | Default | Scope |
|---------|---------|-------|
| `RATE_LIMITING_ENABLED` | True | Master switch |
| `RATE_LIMIT_WEBCHAT_PER_MINUTE` | 30 | `/api/webchat/message/` |
| `RATE_LIMIT_WEBHOOK_PER_MINUTE` | 120 | WhatsApp/Instagram webhooks |
| `RATE_LIMIT_PROVIDER_TEST_PER_MINUTE` | 20 | AI provider test UI |
| `RATE_LIMIT_LOGIN_PER_MINUTE` | 10 | Login form and API |
| `RATE_LIMIT_PLAYGROUND_PER_MINUTE` | 30 | Agent playground POST |

Exceeded limits return HTTP 429 (JSON for API/webhooks) and create an audit log entry.

## Audit Logs (Phase 16)

Workspace audit trail at `/settings/audit-logs/` (owner/admin only).

Logged actions include: login success/failure, team changes, workspace updates, plan switches, integration credential changes, AI provider tests, demo resets, human handoff, rate limit exceeded, unsafe guardrail triggers.

## Release Freeze Security Requirements

| Requirement | Rule |
|-------------|------|
| Demo password | **Must be changed** — default is `Admin123!` |
| DEBUG | **Must be False** in staging and production |
| SECRET_KEY | **Must be unique** — 50+ random characters |
| ALLOWED_HOSTS | **Must be strict** — explicit domain list only |
| CSRF_TRUSTED_ORIGINS | **Must be configured** when DEBUG=False and using HTTPS |
| CREDENTIALS_ENCRYPTION_KEY | **Required** when `INTEGRATIONS_MOCK_MODE=False` |
| Meta live mode | Requires `META_APP_SECRET` and signature validation |
| Backups | Run `scripts/local_backup.py` before major changes |
| Monitoring | **Required before public production** — not in MVP |

## Secrets Handling

- All secrets via environment variables (django-environ)
- `.env` is gitignored — never commit `.env`
- AI API keys optional; mock provider needs none
- Provider settings UI shows key configured yes/no, never the actual key
- Meta credentials required only for live integrations

## Webhook Signature Validation

When `INTEGRATIONS_MOCK_MODE=False`: HMAC-SHA256 validation via `META_APP_SECRET`.

When `INTEGRATIONS_MOCK_MODE=True` (default): signature validation skipped (demo-safe).

## Backups (Phase 16)

```bash
python scripts/local_backup.py      # pg_dump or JSON fallback
python scripts/validate_backup.py   # verify backup files
python scripts/local_restore.py --file backups/backup_xxx.json --confirm
```

See [RUNBOOK.md](RUNBOOK.md) for Docker backup procedures.

## Tenant Isolation Audit

```bash
python scripts/audit_tenant_isolation.py
```

Checks tenant FK presence and selector isolation across CRM, inbox, knowledge, integrations, and agents.

## Security Check Commands

```bash
python manage.py check --deploy
python manage.py check_deploy_ready
python manage.py security_audit
python scripts/check_environment.py
python scripts/audit_tenant_isolation.py
python scripts/validate_backup.py
```

## Admin Password

Demo seed creates `admin@example.com` / `Admin123!`.

Change before external demo:

```bash
python manage.py changepassword admin@example.com
```

Or use **Settings → Security → Change password**.

## Remaining Production Blockers

- HTTPS termination and TLS certificates
- Automated backup scheduling (cron/Celery)
- APM / error monitoring (Sentry, etc.)
- Payment gateway (out of MVP scope)
- Live Meta OAuth (out of MVP scope)
- WAF / DDoS protection at edge

See [FINAL_MVP_ACCEPTANCE_REPORT.md](FINAL_MVP_ACCEPTANCE_REPORT.md) for full acceptance status.
