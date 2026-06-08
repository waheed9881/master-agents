# Security

## Current Security Basics

| Control | Status |
|---------|--------|
| Django session auth | Implemented |
| CSRF protection | Enabled (staff UI and session API) |
| Tenant middleware scoping | Implemented |
| Password validators | Django defaults |
| Webhook CSRF exempt | Only on webhook endpoints |
| X-Frame-Options | DENY in production |
| Secure cookies | Enabled when DEBUG=False |

## Secrets Handling

- All secrets via environment variables (django-environ)
- `.env` is gitignored — never commit `.env`
- `.env.example` contains placeholders only
- `SECRET_KEY` / `DJANGO_SECRET_KEY` must be unique per environment
- AI API keys (`OPENAI_API_KEY`, etc.) optional; mock provider needs none
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

When `INTEGRATIONS_MOCK_MODE=True` (default):

- Signature validation is skipped (safe for local/demo)

## Credential Encryption Placeholder

`ChannelCredential.access_token_encrypted` and `app_secret_encrypted` fields exist but encryption is not fully implemented in MVP.

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
| SECRET_KEY | 50+ char random string |
| ALLOWED_HOSTS | Explicit domain list |
| CSRF_TRUSTED_ORIGINS | HTTPS origins |
| Demo password | Change `admin@example.com` password |
| HTTPS | Required for Meta webhooks |
| Credential encryption | Implement Fernet encryption |
| Rate limiting | Add to webhooks and web chat |
| Admin URL | Consider changing `/admin/` path |
| Database | Use managed Postgres with SSL |
| Redis | Password-protected instance |

## Rate Limiting Recommendations

Not implemented in MVP. Recommended for production:

- `/api/webchat/message/` — 30 req/min per session_key
- `/api/webhooks/whatsapp/` — 100 req/min per IP
- `/api/webhooks/instagram/` — 100 req/min per IP
- `/api/auth/login/` — 10 req/min per IP (brute force protection)

Use django-ratelimit or nginx rate limiting.

## Admin Password

Demo seed creates `admin@example.com` / `Admin123!`.

**Change immediately before any external demo or deployment:**

```bash
python manage.py changepassword admin@example.com
```

Or via Django admin after login.

## ALLOWED_HOSTS / CSRF / CORS

### ALLOWED_HOSTS

Comma-separated in `.env`:
```
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
```

### CSRF_TRUSTED_ORIGINS

Required when using HTTPS and DEBUG=False:
```
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://staging.yourdomain.com
```

### CORS

Not configured in MVP (same-origin UI only). If adding a separate frontend, configure `django-cors-headers` with explicit allowed origins.

## Security Check Commands

```bash
python manage.py check --deploy
python manage.py check_deploy_ready
python scripts/check_environment.py
```
