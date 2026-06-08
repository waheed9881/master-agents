# Release Notes

## AI Agent OS MVP — Phases 1–9

**Version:** MVP 1.2 (Phase 12 complete)  
**Date:** June 2026  
**Status:** Local demo-ready — 10 agent brains, scenario QA, Demo Center

---

## Phase 1 — Foundation

- Django 5 project setup with modular app structure
- Docker Compose (Postgres, Redis, Celery, web)
- Custom user model with email login and roles
- Multi-tenant workspaces with middleware scoping
- Dashboard shell and navigation
- REST API auth endpoints

## Phase 2 — Agent Templates

- 10 agent template catalog with card UI
- Agent deployment flow from template
- Agent instance settings editor
- Agent template and instance APIs
- Sales Closing Agent marked as implemented

## Phase 3 — CRM

- Contacts, leads, pipeline stages, deals, tasks
- Pipeline kanban board UI
- Lead status workflow (new through won/lost)
- CRM REST APIs
- Demo CRM seed data

## Phase 4 — Inbox & Web Chat

- Unified inbox for all channels
- Conversation and message models
- Staff reply, human takeover, re-enable AI
- Web chat demo widget and API
- Django Channels setup for real-time (foundation)

## Phase 5 — Agent Engine

- BaseAgent abstract interface
- SalesClosingAgent full implementation
- AI provider abstraction (mock, OpenAI, Groq, Gemini)
- PromptBuilder with safety rules
- Lead extraction and scoring
- Human handoff decision service
- CRM auto-update from agent runs
- AgentRun and ToolCall logging
- Test message API

## Phase 6 — Knowledge Base

- KnowledgeSource and KnowledgeChunk models
- Auto-chunking on source create
- Keyword search with pricing boost
- Knowledge UI and APIs
- Agent knowledge search integration
- pgvector-ready embedding field

## Phase 7 — Analytics

- Analytics dashboard UI
- KPI overview, funnel, agent/inbox/knowledge metrics
- Recent activity feed
- Date range filters (7/30/90 days)
- Tenant-scoped analytics APIs

## Phase 8 — Integrations Hardening

- WhatsApp and Instagram webhook handlers
- Meta subscription verification
- Signature validation (disabled in mock mode)
- Idempotency via external_message_id
- WebhookEvent audit log
- ChannelCredential model
- Outbound mock sender
- Integrations UI and APIs

## Phase 9 — QA, Docs, Deployment Readiness

- Full documentation suite (14 docs in `docs/`)
- Environment validation script (`scripts/check_environment.py`)
- Deployment readiness command (`python manage.py check_deploy_ready`)
- Smoke test script (`scripts/smoke_test.py`)
- Security hardening in settings (CSRF_TRUSTED_ORIGINS, production cookies)
- `.env.example` completed with comments
- GitHub Actions CI pipeline
- Phase 9 readiness tests
- Updated README

## Phase 10 — Release Freeze, Final Audit, Staging DevOps

- Full repository audit (docs, scripts, settings, routes)
- Route audit script (`scripts/audit_routes.py`)
- API smoke test script (`scripts/api_smoke_test.py`)
- Release checklist (`docs/RELEASE_CHECKLIST.md`)
- Staging deployment plan (`docs/STAGING_DEPLOYMENT_PLAN.md`)
- Final MVP acceptance report (`docs/FINAL_MVP_ACCEPTANCE_REPORT.md`)
- Enhanced environment and deploy readiness checks
- Security doc updates with production blockers
- Doc fixes (webchat route `/inbox/webchat/`)
- Phase 10 release readiness tests

---

## Current MVP Status

| Component | Status |
|-----------|--------|
| Auth & multi-tenancy | Production-ready for staging |
| 10 agent templates | 1 implemented, 9 template-only |
| Sales Closing Agent | Fully working |
| CRM | Complete |
| Inbox & web chat | Complete |
| Knowledge base | Complete (keyword search) |
| Analytics | Complete |
| WhatsApp/Instagram | Mock mode complete, live Meta pending |
| Documentation | Complete |
| CI pipeline | Complete |
| Test suite | 130+ tests passing |
| Release audit | Route + API smoke scripts |

## Demo Credentials

- Email: `admin@example.com`
- Password: `Admin123!`
- **Change before any external deployment**

## Phase 11 — Integrations UI & Agent Brains

- Integrations configuration UI (create/edit/test channels)
- All 10 agent brain modules with shared GenericBusinessAgent architecture
- Agent playground for local testing
- WhatsApp/Instagram mock webhook simulator

## Phase 12 — Agent QA & Demo Polish

- Demo scenario library (5+ scenarios per agent)
- Playground scenario loading with pass/warn quality checks
- Demo Center at `/demo/`
- `scripts/audit_agent_quality.py` for automated scenario QA
- `docs/LOCAL_DEMO_GUIDE.md` with 15/30-minute demo scripts
- Safety prompt hardening across all agents

## Phase 13 — Agent Quality Stabilization

- Intent normalization layer (`intent_normalizer.py`) with global and per-domain aliases
- Domain intent registry (`domain_intents.py`) for all 10 agent domains
- Deterministic intent detection merged with MockAIProvider output
- Scenario evaluation uses normalized intents (PASS / ACCEPTED / WARN / FAIL)
- 60 demo scenarios with canonical expected intents
- Mock provider domain-specific reply styles
- Playground shows normalized intent, raw intent, and match reason
- Demo Center shows scenario count and quality audit target
- Quality audit target: **60 passed, 0 warnings, 0 failed**

## Phase 14 — Real AI Provider Local Testing

- AI provider settings UI at `/settings/ai-providers/`
- Provider test page and API endpoints
- Structured output schema with safe JSON parsing
- Safety guardrails layer for domain-specific rules
- Provider fallback to mock when keys missing or requests fail
- AgentRun tracks provider_name, model_name, fallback_used, metadata_json
- Analytics shows runs by provider, fallback count, token/cost totals
- `AUDIT_AI_PROVIDER=mock` keeps scenario audit deterministic

## Known Limitations

- AI uses MockAIProvider in local demo (keyword-based, not LLM)
- Integrations use mock mode by default
- No vector semantic search
- Credential encryption is placeholder
- No rate limiting on public endpoints
- No billing or subscription management

## What Remains for Live Production

1. Live Meta Cloud API integration (disable mock mode)
3. Fernet credential encryption
4. pgvector semantic search
5. Rate limiting and WAF rules
6. HTTPS infrastructure and secrets manager
7. Database backup automation
8. Monitoring and alerting (Sentry, Datadog, etc.)
9. Remove or secure demo accounts
10. Load testing and performance tuning
