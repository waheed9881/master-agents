# AI Agent OS

Production-minded SaaS platform for business AI agents. Modular monolith architecture with shared agent engine and pluggable agent modules.

## Quick Start (Docker)

```bash
# Copy environment file
cp .env.example .env

# Start all services
docker compose up --build
```

Open http://localhost:8000/login/

### Seed demo data

```bash
docker compose exec web python scripts/seed_demo_data.py
```

**Demo login:**
- Email: `admin@example.com`
- Password: `Admin123!`

> ⚠️ **Change the demo password before deploying to production.**

## Local Development (without Docker)

Requires Python 3.12+, PostgreSQL, and Redis running locally.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: set DATABASE_URL to your local Postgres

python manage.py migrate
python scripts/seed_demo_data.py
python manage.py runserver
```

## Project Structure

```
config/          # Django settings, URLs, Celery, ASGI
apps/
  accounts/      # Custom user model, auth, roles
  tenants/       # Multi-tenant workspaces
  agents/        # Agent templates & instances
  crm/           # Contacts, leads, pipeline, deals, tasks
  inbox/         # Unified messaging inbox
  integrations/  # Web chat, WhatsApp/Instagram webhooks
  knowledge/     # (Phase 6) Knowledge base
  agent_engine/  # (Phase 5) Shared AI orchestration
  agent_modules/ # Agent-specific business logic
templates/       # Django templates (HTMX + Alpine + Tailwind)
scripts/         # Seed and utility scripts
tests/           # pytest test suite
docs/            # Architecture and runbook docs
```

## Tech Stack

- Python 3.12+ / Django 5+ / DRF
- PostgreSQL / Redis / Celery
- Django Channels (real-time inbox)
- HTMX + Alpine.js + Tailwind CSS
- Docker Compose

## Development Phases

| Phase | Status | Scope |
|-------|--------|-------|
| 1 | ✅ Complete | Project setup, Docker, auth, dashboard |
| 2 | ✅ Complete | Agent templates, 10-card UI, deploy flow |
| 3 | ✅ Complete | CRM — contacts, leads, pipeline, tasks |
| 4 | ✅ Complete | Inbox, web chat demo, webhook stubs |
| 5 | ✅ Complete | SalesClosingAgent engine, CRM auto-update |
| 6 | Complete | Knowledge base UI, APIs, agent search |
| 7 | Complete | Analytics dashboard and APIs |
| 8 | Complete | WhatsApp/Instagram webhook hardening |
| 9 | Pending | Tests, docs, seed data |

## API (Phase 1–2)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login/` | Login |
| POST | `/api/auth/logout/` | Logout |
| GET | `/api/me/` | Current user |
| GET | `/api/agent-templates/` | List agent templates |
| GET | `/api/agent-templates/{id}/` | Template detail |
| GET | `/api/agents/` | List tenant agents |
| POST | `/api/agents/` | Deploy agent from template |
| GET | `/api/agents/{id}/` | Agent instance detail |
| PATCH | `/api/agents/{id}/settings/` | Update agent settings |
| GET/POST | `/api/contacts/` | List/create contacts |
| GET/POST | `/api/leads/` | List/create leads |
| GET/PATCH | `/api/leads/{id}/` | Lead detail/update |
| GET | `/api/pipeline/` | Pipeline stages & deals board |
| POST | `/api/tasks/` | Create follow-up task |
| GET | `/api/conversations/` | List conversations |
| GET | `/api/conversations/{id}/` | Conversation detail |
| POST | `/api/conversations/{id}/messages/` | Staff reply |
| POST | `/api/conversations/{id}/human-takeover/` | Human takeover |
| POST | `/api/conversations/{id}/enable-ai/` | Re-enable AI |
| POST | `/api/webchat/message/` | Web chat customer message |
| GET/POST | `/api/webhooks/whatsapp/` | WhatsApp webhook (stub) |
| POST | `/api/webhooks/instagram/` | Instagram webhook (stub) |
| POST | `/api/agent-engine/test-message/` | Test agent with a message |
| GET/POST | `/api/knowledge/` | List/create knowledge sources |
| POST | `/api/knowledge/upload/` | Upload text file as knowledge |
| GET | `/api/analytics/overview/` | Analytics KPI overview |
| GET | `/api/analytics/funnel/` | Lead conversion funnel |
| GET | `/api/analytics/agents/` | Agent performance metrics |
| GET | `/api/analytics/inbox/` | Inbox analytics |
| GET | `/api/analytics/knowledge/` | Knowledge analytics |
| GET | `/api/analytics/recent-activity/` | Recent activity feed |
| GET | `/api/webhooks/whatsapp/` | WhatsApp webhook verify (GET) / inbound (POST) |
| GET | `/api/webhooks/instagram/` | Instagram webhook verify (GET) / inbound (POST) |
| GET | `/api/integrations/channel-accounts/` | List channel accounts |
| GET | `/api/integrations/webhook-events/` | List webhook event log |

## License

Proprietary — AI Agent OS MVP
