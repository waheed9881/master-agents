# AI Agent OS

Production-minded SaaS platform for business AI agents. Modular monolith architecture with a shared agent engine and pluggable agent modules.

**MVP Status:** Phases 1-9 complete. Ready for internal demo, client demo, and staging deployment.

## Product Overview

AI Agent OS lets businesses deploy AI agents for sales, support, and operations across web chat, WhatsApp, and Instagram. The MVP includes:

- Multi-tenant workspaces with role-based access
- 10 agent templates (1 fully implemented: Sales Closing Agent)
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

> **Warning:** Change the demo password before deploying to staging or production.

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

## Test Command

```bash
python -m pytest tests/ -q
```

Other validation:

```bash
python manage.py check
python scripts/check_environment.py
python manage.py check_deploy_ready
python scripts/smoke_test.py
```

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
scripts/         # Seed and utility scripts
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
| [Security](docs/SECURITY.md) | Secrets, webhooks, hardening |
| [QA Checklist](docs/QA_CHECKLIST.md) | Manual acceptance tests |
| [Runbook](docs/RUNBOOK.md) | Operational commands |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common errors and fixes |
| [Release Notes](docs/RELEASE_NOTES.md) | Phase 1-9 summary |

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

## Deployment Note

Before staging or production:

1. Set `DEBUG=False` and a strong `SECRET_KEY`
2. Configure `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`
3. Run `python manage.py check_deploy_ready`
4. Change the demo admin password
5. See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for full checklist

## License

Proprietary — AI Agent OS MVP
