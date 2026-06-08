# AI Agent OS

Production-minded SaaS platform for business AI agents. Modular monolith architecture with a shared agent engine and pluggable agent modules.

**MVP Status:** Phases 1-12 complete. **Local demo-ready** — 10 agent brains, scenario QA, Demo Center, mock integrations. Not approved for public production without security hardening (see limitations below).

## Product Overview

AI Agent OS lets businesses deploy AI agents for sales, support, and operations across web chat, WhatsApp, and Instagram. The MVP includes:

- Multi-tenant workspaces with role-based access
- 10 agent templates (all with active brain modules)
- CRM with leads, pipeline, deals, and tasks
- Unified inbox with human handoff
- Knowledge base with agent-powered search
- Analytics dashboard
- WhatsApp/Instagram webhooks (mock mode for demos)

## Quick Start (Docker)

```bash
cp .env.example .env
docker compose up --build
```

Open http://localhost:8000/login/

Seed demo data:

```bash
docker compose exec web python scripts/seed_demo_data.py
```

**Demo login:**
- Email: `admin@example.com`
- Password: `Admin123!`

> **Staging warning:** Change the demo password before any external demo or staging deployment.

## Quick Start (Local)

Requires Python 3.12+, PostgreSQL, and Redis.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env: set DATABASE_URL to your local Postgres

python manage.py migrate
python scripts/seed_demo_data.py
python manage.py runserver
```

## Demo Center

After seeding, open http://localhost:8000/demo/ for the local demo control room.

See [docs/LOCAL_DEMO_GUIDE.md](docs/LOCAL_DEMO_GUIDE.md) for the full 15/30-minute demo script.

## Validation Commands

```bash
# Full test suite
python -m pytest tests/ -q

# Environment and deployment checks
python manage.py check
python scripts/check_environment.py
python manage.py check_deploy_ready

# Route and API audits
python scripts/smoke_test.py
python scripts/audit_routes.py
python scripts/api_smoke_test.py

# Agent scenario quality audit (target: 60 passed, 0 warnings, 0 failed)
python scripts/audit_agent_quality.py
```

Phase 14 adds AI provider settings at `/settings/ai-providers/`, structured output parsing, safety guardrails, and optional real provider testing via env vars.

## Project Structure

```
config/          # Django settings, URLs, Celery, ASGI
apps/
  accounts/      # Custom user model, auth, roles
  tenants/       # Multi-tenant workspaces
  agents/        # Agent templates and instances
  crm/           # Contacts, leads, pipeline, deals, tasks
  inbox/         # Unified messaging inbox
  integrations/  # Web chat, WhatsApp/Instagram webhooks
  knowledge/     # Knowledge base
  agent_engine/  # Shared AI orchestration
  agent_modules/ # Agent-specific business logic
  analytics/     # Reporting and dashboards
templates/       # Django templates (HTMX + Alpine + Tailwind)
scripts/         # Seed, audit, and validation scripts
tests/           # pytest test suite
docs/            # Architecture, deployment, and runbook docs
```

## Documentation

| Doc | Description |
|-----|-------------|
| [MVP Scope](docs/MVP_SCOPE.md) | What's included and excluded |
| [Architecture](docs/ARCHITECTURE.md) | System design and request flows |
| [Database Schema](docs/DATABASE_SCHEMA.md) | Model reference |
| [Agent Engine](docs/AGENT_ENGINE.md) | AI orchestration details |
| [API Endpoints](docs/API_ENDPOINTS.md) | REST API reference |
| [Integrations](docs/INTEGRATIONS.md) | WhatsApp, Instagram, web chat |
| [Knowledge Base](docs/KNOWLEDGE_BASE.md) | Content and search |
| [Analytics](docs/ANALYTICS.md) | Metrics and dashboards |
| [Deployment](docs/DEPLOYMENT.md) | Local, Docker, staging, production |
| [Staging Plan](docs/STAGING_DEPLOYMENT_PLAN.md) | Staging server deployment guide |
| [Release Checklist](docs/RELEASE_CHECKLIST.md) | Pre-release gate checklist |
| [MVP Acceptance](docs/FINAL_MVP_ACCEPTANCE_REPORT.md) | Final acceptance report |
| [Security](docs/SECURITY.md) | Secrets, webhooks, hardening |
| [QA Checklist](docs/QA_CHECKLIST.md) | Manual acceptance tests |
| [Runbook](docs/RUNBOOK.md) | Operational commands |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common errors and fixes |
| [Release Notes](docs/RELEASE_NOTES.md) | Phase 1-10 summary |

## API Summary

| Area | Key Endpoints |
|------|---------------|
| Auth | `POST /api/auth/login/`, `GET /api/me/` |
| Agents | `GET /api/agent-templates/`, `POST /api/agents/` |
| CRM | `GET /api/leads/`, `GET /api/pipeline/` |
| Inbox | `GET /api/conversations/`, `POST /api/webchat/message/` |
| Agent Engine | `POST /api/agent-engine/test-message/` |
| Knowledge | `GET /api/knowledge/`, `POST /api/knowledge/upload/` |
| Analytics | `GET /api/analytics/overview/` |
| Integrations | `GET /api/integrations/webhook-events/` |
| Webhooks | `GET/POST /api/webhooks/whatsapp/`, `GET/POST /api/webhooks/instagram/` |

Full reference: [docs/API_ENDPOINTS.md](docs/API_ENDPOINTS.md)

## Tech Stack

- Python 3.12+ / Django 5+ / DRF
- PostgreSQL / Redis / Celery
- Django Channels (real-time inbox)
- HTMX + Alpine.js + Tailwind CSS
- Docker Compose
- GitHub Actions CI

## Development Phases

| Phase | Status | Scope |
|-------|--------|-------|
| 1 | Complete | Project setup, Docker, auth, dashboard |
| 2 | Complete | Agent templates, 10-card UI, deploy flow |
| 3 | Complete | CRM — contacts, leads, pipeline, tasks |
| 4 | Complete | Inbox, web chat demo, webhook stubs |
| 5 | Complete | SalesClosingAgent engine, CRM auto-update |
| 6 | Complete | Knowledge base UI, APIs, agent search |
| 7 | Complete | Analytics dashboard and APIs |
| 8 | Complete | WhatsApp/Instagram webhook hardening |
| 9 | Complete | Docs, CI, security, deployment readiness |
| 10 | Complete | Release freeze, audit, staging DevOps |

## Staging Deployment

1. Follow [docs/STAGING_DEPLOYMENT_PLAN.md](docs/STAGING_DEPLOYMENT_PLAN.md)
2. Complete [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md)
3. Set `DEBUG=False`, strong `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`
4. Run `python manage.py check_deploy_ready`
5. Change demo admin password

## Production Limitations

This MVP is **not production-ready** without addressing:

- Default demo credentials (`Admin123!`)
- Mock AI provider and mock Meta integrations (by default)
- No rate limiting on webhooks or web chat
- Credential encryption is placeholder only
- No automated backups or monitoring
- Only 1 of 10 agent modules implemented

See [docs/SECURITY.md](docs/SECURITY.md) and [docs/FINAL_MVP_ACCEPTANCE_REPORT.md](docs/FINAL_MVP_ACCEPTANCE_REPORT.md).

## License

Proprietary — AI Agent OS MVP
