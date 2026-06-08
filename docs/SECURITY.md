# Security

## Current Security Basics

| Control | Status |
|---------|--------|
| Django session auth | Implemented |
| CSRF protection | Enabled (staff UI and session API) |
| Tenant middleware scoping | Implemented |
| Role-based access (owner/admin/manager/rep) | Implemented (Phase 15) |
| Settings/team restricted to owner/admin | Implemented |
| Sales rep blocked from analytics/settings | Implemented |
| Password validators | Django defaults |
| Webhook CSRF exempt | Only on webhook endpoints |
| X-Frame-Options | DENY in production |
| Secure cookies | Enabled when DEBUG=False |

## Release Freeze Security Requirements

The following are **mandatory** before staging or production deployment:

| Requirement | Rule |
|-------------|------|
| Demo password | **Must be changed** — default is `Admin123!` |
| DEBUG | **Must be False** in staging and production |
| SECRET_KEY | **Must be unique** — 50+ random characters, never use defaults |
| ALLOWED_HOSTS | **Must be strict** — explicit domain list only, no wildcards |
| CSRF_TRUSTED_ORIGINS | **Must be configured** when DEBUG=False and using HTTPS |
| Meta live mode | **Requires real signature validation** — set `INTEGRATIONS_MOCK_MODE=False` and configure `META_APP_SECRET` |
| Credential encryption | **Placeholder only** — Fernet encryption not fully implemented in MVP |
| Webhook rate limiting | **Required before production** — not implemented in MVP |
| Backups | **Required before production** — manual procedure documented in RUNBOOK |
| Monitoring | **Required before production** — no APM/error tracking in MVP |

## Secrets Handling

- All secrets via environment variables (django-environ)
- `.env` is gitignored — never commit `.env`
- `.env.example` contains placeholders only
- `SECRET_KEY` / `DJANGO_SECRET_KEY` must be unique per environment
- AI API keys (`OPENAI_API_KEY`, etc.) optional; mock provider needs none
- **Never commit real API keys** — use `.env` locally only
- Provider settings UI shows key configured yes/no, never the actual key
- Scenario audit (`audit_agent_quality.py`) forces `AUDIT_AI_PROVIDER=mock` by default
- Meta credentials (`META_APP_SECRET`, `META_ACCESS_TOKEN`) required only for live integrations

## .env Rules

1. Copy `.env.example` to `.env` for local dev
2. Never commit `.env` to version control
3. Use secrets manager (AWS Secrets Manager, Vault, etc.) in production
4. Rotate `SECRET_KEY` if compromised (invalidates all sessions)
5. Generate `CREDENTIALS_ENCRYPTION_KEY` with Fernet for future credential encryption

## Webhook Signature Validation

When `INTEGRATIONS_MOCK_MODE=False`:

- Meta sends `X-Hub-Signature-256` header
- Server validates HMAC-SHA256 using `META_APP_SECRET`
- Invalid signatures return 403
- **Live Meta mode requires real signature validation** — do not disable in production

When `INTEGRATIONS_MOCK_MODE=True` (default):

- Signature validation is skipped (safe for local/demo only)

## Credential Encryption Placeholder

`ChannelCredential.access_token_encrypted` and `app_secret_encrypted` fields exist but **encryption is not fully implemented** in MVP. Values may be stored without Fernet encryption until `CREDENTIALS_ENCRYPTION_KEY` integration is completed.

Set `CREDENTIALS_ENCRYPTION_KEY` (Fernet key) for future use:

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

## Production Hardening Required

Before public production launch:

| Item | Action |
|------|--------|
| DEBUG | Set False |
| SECRET_KEY | 50+ char random string, unique per environment |
| ALLOWED_HOSTS | Explicit domain list, no `*` wildcard |
| CSRF_TRUSTED_ORIGINS | HTTPS origins matching your domain |
| Demo password | Change `admin@example.com` password or remove account |
| HTTPS | Required for Meta webhooks |
| Credential encryption | Implement Fernet encryption |
| Rate limiting | Add to webhooks and web chat (required) |
| Backups | Automated database backups (required) |
| Monitoring | Error tracking and uptime checks (required) |
| Admin URL | Consider changing `/admin/` path |
| Database | Use managed Postgres with SSL |
| Redis | Password-protected instance |

## Rate Limiting Recommendations

**Not implemented in MVP. Required before production.**

Recommended limits:

- `/api/webchat/message/` — 30 req/min per session_key
- `/api/webhooks/whatsapp/` — 100 req/min per IP
- `/api/webhooks/instagram/` — 100 req/min per IP
- `/api/auth/login/` — 10 req/min per IP (brute force protection)

Use django-ratelimit or nginx rate limiting.

## Admin Password

Demo seed creates `admin@example.com` / `Admin123!`.

**Change immediately before any external demo, staging, or production deployment:**

```bash
python manage.py changepassword admin@example.com
```

Or via Django admin after login.

## ALLOWED_HOSTS / CSRF / CORS

### ALLOWED_HOSTS

Must be strict — list only domains that should reach the app:

```
ALLOWED_HOSTS=staging.yourdomain.com
```

Never use `*` in production.

### CSRF_TRUSTED_ORIGINS

Required when using HTTPS and DEBUG=False:

```
CSRF_TRUSTED_ORIGINS=https://staging.yourdomain.com
```

### CORS

Not configured in MVP (same-origin UI only). If adding a separate frontend, configure `django-cors-headers` with explicit allowed origins.

## Security Check Commands

```bash
python manage.py check --deploy
python manage.py check_deploy_ready
python scripts/check_environment.py
```

See also [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) for pre-release security gate.
