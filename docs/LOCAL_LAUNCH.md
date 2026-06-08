# Local Launch Guide

Quick start for Windows local demos of AI Agent OS.

---

## Prerequisites

- Python 3.12+ recommended (3.10+ supported)
- PostgreSQL running locally (or Docker Compose)
- Redis (optional for Channels; rate limit falls back to memory)

---

## One-click launch (Windows)

### Batch

```bat
run_local_demo.bat
```

### PowerShell

```powershell
.\run_local_demo.ps1
```

This will:

1. Activate `.venv` if present
2. Run migrations
3. Seed demo data
4. Run environment check
5. Start server at `http://127.0.0.1:8000`

### Full validation suite

```bat
run_local_checks.bat
```

or

```powershell
.\run_local_checks.ps1
```

---

## Manual setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python scripts\seed_demo_data.py
python manage.py runserver
```

---

## Demo login

| Field | Value |
|-------|-------|
| Email | admin@example.com |
| Password | Admin123! |

Change via **Settings -> Security -> Change password** before external demos.

---

## Key URLs

| Page | URL |
|------|-----|
| Dashboard | http://127.0.0.1:8000/dashboard/ |
| Demo Center | http://127.0.0.1:8000/demo/ |
| Demo Report | http://127.0.0.1:8000/demo/report/ |
| Agents | http://127.0.0.1:8000/agents/ |
| Integrations | http://127.0.0.1:8000/integrations/ |
| Security | http://127.0.0.1:8000/settings/security/ |

---

## Docker note

If using Docker Compose, set `DATABASE_URL` and `REDIS_URL` in `.env` to match compose services. See `docs/RUNBOOK.md` for backup commands.

---

## PostgreSQL note

Default local connection: `postgres://aiagent:aiagent@localhost:5432/ai_agent_os`

Create database if needed:

```sql
CREATE USER aiagent WITH PASSWORD 'aiagent';
CREATE DATABASE ai_agent_os OWNER aiagent;
```

---

## Health checks

```powershell
python manage.py check
python scripts/check_environment.py
python manage.py security_audit
python scripts/smoke_test.py
python scripts/audit_agent_quality.py
```

Target: scenario audit **60 passed, 0 warnings, 0 failed**.

---

## Common issues

| Issue | Solution |
|-------|----------|
| Database connection refused | Start PostgreSQL; verify `DATABASE_URL` in `.env` |
| Redis unavailable | WARN only — app works; start Redis for Channels |
| pg_dump version mismatch | `local_backup.py` falls back to JSON export |
| Port 8000 in use | `python manage.py runserver 8001` |
| Stale demo data | `python manage.py reset_demo_data --safe --reseed` |

See `docs/TROUBLESHOOTING.md` for more.
