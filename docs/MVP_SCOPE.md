# MVP Scope

## What the MVP Includes

AI Agent OS MVP is a multi-tenant Django SaaS platform for deploying and operating business AI agents. The current release includes:

| Area | Status | Details |
|------|--------|---------|
| Auth & tenants | Complete | Email login, roles, tenant scoping |
| Dashboard | Complete | Workspace overview |
| Agent templates | Complete | 10-card catalog UI |
| Agent deployment | Complete | Deploy from template, settings editor |
| CRM | Complete | Contacts, leads, pipeline, deals, tasks |
| Inbox | Complete | Unified conversations, staff replies |
| Web chat | Complete | Demo widget + API |
| Agent engine | Complete | Shared orchestration, tool logging |
| Sales Closing Agent | Complete | Full AI flow with CRM auto-update |
| Knowledge base | Complete | Sources, chunks, agent search |
| Analytics | Complete | KPIs, funnel, agent/inbox/knowledge metrics |
| Integrations | Complete | WhatsApp/Instagram webhooks (mock mode) |
| Docker | Complete | Postgres, Redis, Celery, web |

## Fully Working Agent

**WhatsApp + Instagram Sales Closing Agent** (`sales-closing-agent`) is the only agent with a complete implementation:

- Inbound message understanding (mock or live AI provider)
- Knowledge base search and prompt injection
- Lead extraction and scoring
- CRM auto-update (contact, lead, tasks)
- Hot lead detection
- Human handoff rules
- Works via web chat, WhatsApp mock webhook, Instagram mock webhook

## Template-Only Agents (9)

These appear in the catalog with metadata and deploy UI but have no agent class wired to the orchestrator:

1. Real Estate AI Sales Agent (`real-estate-agent`)
2. Clinic Receptionist + Patient Follow-up Agent (`clinic-agent`)
3. Home Services / Contractor Bidding Agent (`home-services-agent`)
4. School / Academy Admin Agent (`school-agent`)
5. AI Voice Receptionist for SMEs (`voice-agent`)
6. AI Tender / Proposal Writing Agent (`tender-agent`)
7. eCommerce Support + Order Tracking Agent (`ecommerce-agent`)
8. AI Recruitment Screening Agent (`recruitment-agent`)
9. AI Finance / Bookkeeping Assistant (`finance-agent`)

Deploying a template-only agent creates an `AgentInstance` record but inbound messages will not receive AI replies until a module is implemented.

## Intentionally Excluded from MVP

- Live Meta WhatsApp/Instagram outbound messaging (mock sender only)
- Vector embeddings / pgvector semantic search (keyword fallback only)
- Billing, subscriptions, and payment processing
- SSO / OAuth social login
- Mobile apps
- Real-time voice agents
- Multi-language admin UI
- Advanced RBAC beyond four roles
- Email/SMS channel integrations
- Automated test coverage for all 10 agents
- Horizontal scaling / Kubernetes manifests
- Credential encryption at rest (placeholder fields only)

## Future Roadmap

| Phase | Focus |
|-------|-------|
| Post-MVP | Implement remaining 9 agent modules one by one |
| Post-MVP | Live Meta Cloud API (disable mock mode) |
| Post-MVP | pgvector semantic knowledge search |
| Post-MVP | Rate limiting and API keys for public endpoints |
| Post-MVP | Production credential encryption (Fernet) |
| Post-MVP | Email notifications for hot leads and handoffs |
| Post-MVP | Extract agent modules into separate deployable services |
| Post-MVP | Billing and usage metering |
