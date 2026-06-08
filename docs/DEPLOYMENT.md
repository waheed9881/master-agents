# Deployment

## Local Run (without Docker)

### Prerequisites

- Python 3.12+
- PostgreSQL 16+
- Redis 7+

### Steps

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env: set DATABASE_URL to local Postgres

python manage.py migrate
python scripts/seed_demo_data.py
python manage.py runserver
```

Open http://localhost:8000/login/

## Docker Run

```bash
cp .env.example .env
docker compose up --build
```

Services started:
- `postgres` — port 5432
- `redis` — port 6379
- `web` — port 8000 (migrate + collectstatic + runserver)
- `celery_worker`
- `celery_beat`

Seed demo data:
```bash
docker compose exec web python scripts/seed_demo_data.py
```

## Environment Variables

See `.env.example` for full list. Critical vars:

| Variable | Staging | Production |
|----------|---------|------------|
| DEBUG | False | False |
| SECRET_KEY | Random 50+ chars | Random 50+ chars |
| ALLOWED_HOSTS | staging.example.com | app.example.com |
| CSRF_TRUSTED_ORIGINS | https://staging.example.com | https://app.example.com |
| DATABASE_URL | Postgres connection | Postgres connection |
| REDIS_URL | Redis connection | Redis connection |
| AI_PROVIDER | mock or live | openai/groq/gemini |
| INTEGRATIONS_MOCK_MODE | True (until Meta ready) | False when live |

## Database Migrations

```bash
python manage.py migrate
python manage.py showmigrations
```

In Docker:
```bash
docker compose exec web python manage.py migrate
```

## Static Files

```bash
python manage.py collectstatic --noinput
```

Docker web service runs collectstatic on startup. For production behind nginx, serve `staticfiles/` directory.

## Celery / Redis

Celery worker and beat are defined in `docker-compose.yml`.

Check worker:
```bash
docker compose logs celery_worker
# or locally:
celery -A config worker -l info
```

Check Redis:
```bash
redis-cli ping
# Expected: PONG
```

## Webhook Public URL Requirements

Meta webhooks require a **public HTTPS** endpoint:

- WhatsApp: `https://yourdomain.com/api/webhooks/whatsapp/`
- Instagram: `https://yourdomain.com/api/webhooks/instagram/`

For local testing use ngrok or similar tunnel. Set `INTEGRATIONS_MOCK_MODE=True` for local dev without Meta.

## Staging Deployment Checklist

- [ ] Copy `.env.example` to `.env`, set staging values
- [ ] `DEBUG=False`
- [ ] Generate strong `SECRET_KEY`
- [ ] Set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`
- [ ] PostgreSQL provisioned and `DATABASE_URL` set
- [ ] Redis provisioned and `REDIS_URL` set
- [ ] `python manage.py migrate`
- [ ] `python manage.py collectstatic --noinput`
- [ ] `python scripts/check_environment.py`
- [ ] `python manage.py check_deploy_ready`
- [ ] Start web + celery_worker + celery_beat
- [ ] Run `python scripts/seed_demo_data.py` (optional for demo)
- [ ] Change demo admin password
- [ ] `AI_PROVIDER=mock` unless API keys configured
- [ ] `INTEGRATIONS_MOCK_MODE=True` unless Meta configured
- [ ] Run `python -m pytest tests/ -q`

## Production Deployment Checklist

All staging items plus:

- [ ] HTTPS terminated at load balancer or reverse proxy
- [ ] `SECURE_SSL_REDIRECT=True` (if not handled by proxy)
- [ ] Database backups scheduled (see RUNBOOK.md)
- [ ] Remove or disable demo seed account password
- [ ] Live AI provider keys in secrets manager
- [ ] Meta credentials configured if using live integrations
- [ ] Log aggregation configured
- [ ] Health check endpoint monitored
- [ ] Rate limiting on public webhooks (recommended)

## Pre-Deploy Validation

```bash
python manage.py check
python manage.py check_deploy_ready
python scripts/check_environment.py
python -m pytest tests/ -q
```

## Backup / Restore

See RUNBOOK.md for backup and restore commands.
