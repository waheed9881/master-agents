# Troubleshooting

Common errors and fixes for AI Agent OS development and deployment.

---

## PostgreSQL role/database missing

**Error:** `FATAL: role "aiagent" does not exist` or `database "ai_agent_os" does not exist`

**Fix (Docker):**
```bash
docker compose down -v
docker compose up --build
```

**Fix (local):**
```sql
CREATE USER aiagent WITH PASSWORD 'aiagent';
CREATE DATABASE ai_agent_os OWNER aiagent;
```

Update `.env` `DATABASE_URL` to match your credentials.

---

## Docker not running

**Error:** `Cannot connect to the Docker daemon`

**Fix:**
- Start Docker Desktop (Windows/Mac)
- Verify: `docker ps`
- Retry: `docker compose up --build`

---

## Migration issues

**Error:** `django.db.migrations.exceptions.InconsistentMigrationHistory`

**Fix:**
```bash
python manage.py showmigrations
python manage.py migrate --plan
```

If dev database is corrupted:
```bash
python manage.py flush --noinput
python manage.py migrate
python scripts/seed_demo_data.py
```

Never use `--fake` in production without understanding the impact.

---

## Port already in use

**Error:** `Error: That port is already in use` (8000, 5432, 6379)

**Fix:**
```bash
# Find process on port 8000 (Windows):
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# Or change port:
python manage.py runserver 8001
```

For Docker port conflicts, stop other containers using the same ports.

---

## Redis/Celery not running

**Symptoms:** Inbox real-time updates fail, Celery tasks not processed

**Fix:**
```bash
redis-cli ping
# Expected: PONG

# Docker:
docker compose up redis celery_worker celery_beat
docker compose logs celery_worker
```

Web chat and agent engine work without Celery; async tasks may queue until worker starts.

---

## Git push issues

**Error:** `rejected` or `non-fast-forward`

**Fix:**
```bash
git pull --rebase origin <branch>
git push origin <branch>
```

Do not force push to main/master without team approval.

---

## Windows encoding issues

**Symptoms:** UnicodeEncodeError, garbled console output

**Fix:**
```powershell
$env:PYTHONIOENCODING = "utf-8"
chcp 65001
```

Use ASCII-only scripts (`check_environment.py` is ASCII-safe).

Avoid emojis in print statements on Windows cp1252 consoles.

---

## Webhook verification failure

**Error:** GET webhook returns 403

**Causes:**
- `hub.verify_token` does not match `META_VERIFY_TOKEN`
- `hub.mode` is not `subscribe`

**Fix:**
```bash
# Test locally:
curl "http://localhost:8000/api/webhooks/whatsapp/?hub.mode=subscribe&hub.verify_token=ai-agent-os-verify&hub.challenge=test123"
# Expected: test123
```

Check `.env`: `META_VERIFY_TOKEN=ai-agent-os-verify`

---

## Missing AI API keys

**Symptoms:** Agent replies work but use mock responses when live provider expected

**Fix:**
- Set `AI_PROVIDER=mock` for demos (no key needed)
- For live provider, set matching API key:
  - `AI_PROVIDER=openai` + `OPENAI_API_KEY=sk-...`
  - `AI_PROVIDER=groq` + `GROQ_API_KEY=gsk_...`
  - `AI_PROVIDER=gemini` + `GEMINI_API_KEY=...`

Providers automatically fall back to mock if key is missing.

---

## Meta signature invalid

**Error:** POST webhook returns 403 `Invalid signature`

**Causes:**
- `INTEGRATIONS_MOCK_MODE=False` but signature not computed correctly
- Wrong `META_APP_SECRET`

**Fix for local dev:**
```
INTEGRATIONS_MOCK_MODE=True
```

**Fix for live:**
- Verify `META_APP_SECRET` matches Meta Developer App
- Ensure raw request body is used for HMAC (not re-serialized JSON)
- Meta must send `X-Hub-Signature-256` header

---

## SECRET_KEY warnings

**Warning from check_deploy_ready:** insecure SECRET_KEY

**Fix:**
```python
import secrets
print(secrets.token_urlsafe(50))
```

Set in `.env`:
```
SECRET_KEY=<generated-value>
```

---

## Static files not loading

**Symptoms:** CSS/JS missing in production

**Fix:**
```bash
python manage.py collectstatic --noinput
```

Configure web server to serve `/static/` from `staticfiles/` directory.

---

## Tests fail with database errors

**Fix:**
```bash
# Ensure test database can be created
python manage.py migrate
python -m pytest tests/ -q --create-db
```

In CI, PostgreSQL service must be healthy before tests run.

---

## Cannot login after seed

**Fix:**
```bash
python scripts/seed_demo_data.py
# Resets password to Admin123!
```

Or:
```bash
python manage.py changepassword admin@example.com
```
