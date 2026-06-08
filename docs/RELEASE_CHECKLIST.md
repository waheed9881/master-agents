# Release Checklist

Use this checklist before internal demo, client demo, or staging deployment.

Mark each item PASS / FAIL / N/A. All required items must PASS.

---

## Local Checks

- [ ] `python manage.py check` passes
- [ ] `python manage.py migrate` — no pending migrations
- [ ] `python scripts/seed_demo_data.py` completes without error
- [ ] App loads at http://localhost:8000/login/
- [ ] Demo login works (`admin@example.com` / `Admin123!`)
- [ ] `.env` exists locally (not committed)

## Test Checks

- [ ] `python -m pytest tests/ -q` — all tests pass
- [ ] `python scripts/smoke_test.py` — all routes PASS
- [ ] `python scripts/audit_routes.py` — all routes PASS
- [ ] `python scripts/api_smoke_test.py` — all APIs PASS

## Environment Checks

- [ ] `python scripts/check_environment.py` — no FAIL results
- [ ] `python manage.py check_deploy_ready` — review all warnings
- [ ] `SECRET_KEY` is not a default value (staging/production)
- [ ] `DEBUG=False` for staging/production

## Docker Checks

- [ ] `docker compose up --build` starts all services
- [ ] Postgres healthcheck passes
- [ ] Redis healthcheck passes
- [ ] Web service runs migrations on startup
- [ ] `docker compose exec web python scripts/seed_demo_data.py` works
- [ ] App accessible at http://localhost:8000

## CI Checks

- [ ] `.github/workflows/ci.yml` exists
- [ ] CI runs on push to main/master and phase-* branches
- [ ] CI uses PostgreSQL service (no external DB)
- [ ] CI uses `AI_PROVIDER=mock` and `INTEGRATIONS_MOCK_MODE=True`
- [ ] Latest CI run is green

## Security Checks

- [ ] No secrets in git (no `.env`, no API keys in code)
- [ ] Demo password will be changed before external access
- [ ] `ALLOWED_HOSTS` includes staging domain only (no wildcards)
- [ ] `CSRF_TRUSTED_ORIGINS` set for HTTPS staging URL
- [ ] `INTEGRATIONS_MOCK_MODE=True` unless Meta is fully configured
- [ ] Review [SECURITY.md](SECURITY.md) production requirements

## Staging Environment Checks

- [ ] PostgreSQL provisioned and reachable
- [ ] Redis provisioned and reachable
- [ ] Environment variables set per [STAGING_DEPLOYMENT_PLAN.md](STAGING_DEPLOYMENT_PLAN.md)
- [ ] `collectstatic` run if serving static files via proxy
- [ ] Celery worker and beat running
- [ ] HTTPS configured at reverse proxy
- [ ] Webhook URLs registered in Meta (if live integrations)

## Demo User / Password Warning

- [ ] Team notified: default password is `Admin123!`
- [ ] Password changed OR staging is internal-only with network restrictions
- [ ] Demo account email documented for handoff

## Backup Check

- [ ] Database backup taken before first staging deploy
- [ ] Backup restore procedure tested (see [RUNBOOK.md](RUNBOOK.md))
- [ ] Backup schedule defined for staging

## Rollback Plan

If staging deploy fails:

1. Stop web, celery_worker, celery_beat containers/processes
2. Restore database from pre-deploy backup
3. Revert to previous Docker image or git tag
4. Verify with `python scripts/audit_routes.py`
5. Notify team with failure summary

Document rollback owner: _______________

## Post-Deployment Smoke Tests

Run after staging is live:

```bash
python scripts/audit_routes.py
python scripts/api_smoke_test.py
python scripts/check_environment.py
```

Manual checks:

- [ ] Login page loads over HTTPS
- [ ] Dashboard, agents, CRM, inbox, knowledge, analytics load
- [ ] Web chat demo sends and receives reply
- [ ] WhatsApp webhook verify returns challenge (GET with verify token)
- [ ] Analytics overview API returns data

---

**Release manager:** _______________  
**Date:** _______________  
**Target:** internal demo / client demo / staging  
**Overall result:** GO / NO-GO
