# Runbook

Operational commands for AI Agent OS.

## Run App

### Local
```bash
python manage.py runserver
# or specific port:
python manage.py runserver 0.0.0.0:8000
```

### Docker
```bash
docker compose up
# detached:
docker compose up -d
```

## Migrate

```bash
python manage.py migrate
python manage.py showmigrations
```

Docker:
```bash
docker compose exec web python manage.py migrate
```

## Seed Demo Data

```bash
python scripts/seed_demo_data.py
```

Individual seeds:
```bash
python scripts/seed_agent_templates.py
python scripts/seed_crm_demo.py
python scripts/seed_inbox_demo.py
python scripts/seed_knowledge_demo.py
python scripts/seed_integrations_demo.py
```

Docker:
```bash
docker compose exec web python scripts/seed_demo_data.py
```

## Reset Demo Data

No automated reset script. To reset:

```bash
# WARNING: destroys all data
python manage.py flush --noinput
python manage.py migrate
python scripts/seed_demo_data.py
```

Docker:
```bash
docker compose exec web python manage.py flush --noinput
docker compose exec web python scripts/seed_demo_data.py
```

Or reset database volume:
```bash
docker compose down -v
docker compose up --build
docker compose exec web python scripts/seed_demo_data.py
```

## Run Tests

```bash
python -m pytest tests/ -q
# verbose:
python -m pytest tests/ -v
# single file:
python -m pytest tests/test_phase9_readiness.py -v
```

## Create Superuser

```bash
python manage.py createsuperuser
```

## Check Celery

```bash
# Worker logs (Docker):
docker compose logs -f celery_worker

# Beat logs:
docker compose logs -f celery_beat

# Local worker:
celery -A config worker -l info

# Local beat:
celery -A config beat -l info
```

## Check Redis

```bash
redis-cli ping
# Expected: PONG

# Docker:
docker compose exec redis redis-cli ping
```

## View Logs

```bash
# Docker all services:
docker compose logs -f

# Web only:
docker compose logs -f web

# Local Django:
# logs go to stdout where runserver is running
```

## Environment Checks

```bash
python scripts/check_environment.py
python manage.py check
python manage.py check --deploy
python manage.py check_deploy_ready
python scripts/smoke_test.py
```

## Static Files

```bash
python manage.py collectstatic --noinput
```

## Backup Database

### Automated local script (Phase 16)

```bash
python scripts/local_backup.py
python scripts/validate_backup.py
```

Creates timestamped files in `backups/` — tries `pg_dump` first, falls back to JSON fixture export.

Restore (destructive — requires `--confirm`):

```bash
python scripts/local_restore.py --file backups/backup_YYYYMMDD_HHMMSS.json --confirm
```

### Docker Postgres
```bash
docker compose exec postgres pg_dump -U aiagent ai_agent_os > backup_$(date +%Y%m%d).sql
```

### Windows PowerShell
```powershell
docker compose exec postgres pg_dump -U aiagent ai_agent_os > backup.sql
```

### Local Postgres
```bash
pg_dump -U aiagent ai_agent_os > backup.sql
```

## Restore Database

```bash
# Docker:
cat backup.sql | docker compose exec -T postgres psql -U aiagent ai_agent_os

# Windows PowerShell:
Get-Content backup.sql | docker compose exec -T postgres psql -U aiagent ai_agent_os
```

## Common Windows Commands

```powershell
# Activate venv
.venv\Scripts\activate

# Install deps
pip install -r requirements.txt

# Copy env
copy .env.example .env

# Run server
python manage.py runserver

# Run tests
python -m pytest tests/ -q

# Docker
docker compose up --build
docker compose exec web python manage.py migrate
docker compose exec web python scripts/seed_demo_data.py
```

## Change Demo Password

```bash
python manage.py changepassword admin@example.com
```

## Django Shell

```bash
python manage.py shell
```

## Stop Services

```bash
docker compose down
# remove volumes:
docker compose down -v
```
