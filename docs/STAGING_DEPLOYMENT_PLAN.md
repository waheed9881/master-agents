# Staging Deployment Plan

Step-by-step guide for deploying AI Agent OS to a staging server.

---

## Recommended Server Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 vCPU | 4 vCPU |
| RAM | 4 GB | 8 GB |
| Disk | 20 GB SSD | 40 GB SSD |
| OS | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |

Services required on or reachable from the server:
- Docker 24+ and Docker Compose v2
- Public HTTPS endpoint (reverse proxy)
- Outbound internet for package installs (not for MVP runtime if using mock AI)

---

## PostgreSQL Setup

### Option A: Docker Compose (included)

The project `docker-compose.yml` includes Postgres 16. Data persists in `postgres_data` volume.

Default credentials (change for staging):
- Database: `ai_agent_os`
- User: `aiagent`
- Password: `aiagent`

### Option B: Managed PostgreSQL

Use AWS RDS, DigitalOcean Managed DB, or similar.

Set in `.env`:
```
DATABASE_URL=postgres://USER:PASSWORD@HOST:5432/ai_agent_os
```

Enable SSL if provider supports it.

---

## Redis Setup

### Option A: Docker Compose (included)

Redis 7 runs on port 6379 inside compose network.

### Option B: Managed Redis

```
REDIS_URL=redis://:PASSWORD@HOST:6379/0
CELERY_BROKER_URL=redis://:PASSWORD@HOST:6379/1
```

---

## Environment Variables

Copy `.env.example` to `.env` on the staging server.

**Required for staging:**

```bash
DEBUG=False
SECRET_KEY=<generate-50-char-random-string>
ALLOWED_HOSTS=staging.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://staging.yourdomain.com

DATABASE_URL=postgres://...
REDIS_URL=redis://...
CELERY_BROKER_URL=redis://...

AI_PROVIDER=mock
INTEGRATIONS_MOCK_MODE=True
META_VERIFY_TOKEN=ai-agent-os-verify
```

Generate SECRET_KEY:
```python
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for full variable reference.

---

## Docker Compose Staging Flow

```bash
# 1. Clone repository
git clone <repo-url> ai-agent-os
cd ai-agent-os

# 2. Configure environment
cp .env.example .env
# Edit .env with staging values

# 3. Build and start
docker compose up --build -d

# 4. Verify services
docker compose ps
docker compose logs web --tail=50

# 5. Seed demo data (optional for demo staging)
docker compose exec web python scripts/seed_demo_data.py

# 6. Run validation
docker compose exec web python scripts/check_environment.py
docker compose exec web python manage.py check_deploy_ready
docker compose exec web python scripts/audit_routes.py
docker compose exec web python scripts/api_smoke_test.py
```

---

## Migration Commands

Migrations run automatically on web container startup. To run manually:

```bash
docker compose exec web python manage.py migrate --noinput
docker compose exec web python manage.py showmigrations
```

---

## Seed / Demo Commands

```bash
# Full demo dataset
docker compose exec web python scripts/seed_demo_data.py

# Individual seeds
docker compose exec web python scripts/seed_crm_demo.py
docker compose exec web python scripts/seed_knowledge_demo.py
```

**Warning:** Change `admin@example.com` password after seeding:
```bash
docker compose exec web python manage.py changepassword admin@example.com
```

---

## Collectstatic

Run when serving static files through nginx or a CDN:

```bash
docker compose exec web python manage.py collectstatic --noinput
```

Static files output: `staticfiles/` directory.

The Docker web service runs collectstatic on startup.

---

## Reverse Proxy Notes

Recommended: nginx or Caddy in front of the Django app.

Example nginx upstream:
```
upstream ai_agent_os {
    server 127.0.0.1:8000;
}
```

Proxy headers to set:
```
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
```

For WebSocket support (Channels), configure upgrade headers if needed.

---

## HTTPS Notes

- Meta webhooks require public HTTPS
- Set `CSRF_TRUSTED_ORIGINS=https://staging.yourdomain.com`
- Terminate TLS at reverse proxy (Let's Encrypt recommended)
- If proxy handles HTTPS, keep `SECURE_SSL_REDIRECT=False` unless Django should redirect

---

## Webhook Public URL Notes

Register these URLs in Meta Developer Console (when going live):

| Channel | URL |
|---------|-----|
| WhatsApp | `https://staging.yourdomain.com/api/webhooks/whatsapp/` |
| Instagram | `https://staging.yourdomain.com/api/webhooks/instagram/` |

Verify token must match `META_VERIFY_TOKEN` in `.env`.

For staging demos with mock mode, webhooks can be tested via curl without Meta registration.

---

## Celery Worker Notes

Staging should run all three background services:

```bash
docker compose up -d celery_worker celery_beat
```

Check status:
```bash
docker compose logs -f celery_worker
docker compose logs -f celery_beat
```

Celery is optional for core demo flows but recommended for parity with production.

---

## Log Checking Commands

```bash
# All services
docker compose logs -f

# Web only
docker compose logs -f web

# Errors in last 100 lines
docker compose logs web --tail=100 | grep -i error
```

Windows PowerShell:
```powershell
docker compose logs web --tail=100
```

---

## Staging Validation Checklist

After deploy, confirm:

1. `python manage.py check` — PASS
2. `python scripts/check_environment.py` — no FAIL
3. `python manage.py check_deploy_ready` — review warnings
4. `python scripts/audit_routes.py` — PASS
5. `python scripts/api_smoke_test.py` — PASS
6. HTTPS login works
7. Demo password changed or access restricted

See [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) for full release gate.
