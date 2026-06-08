# QA Checklist

Human acceptance checklist for demo, staging, and release validation.

Mark each item PASS / FAIL / N/A. All core items should PASS before client demo.

---

## Authentication

- [ ] Login page loads at `/login/`
- [ ] Login with `admin@example.com` / `Admin123!` succeeds
- [ ] Invalid credentials show error message
- [ ] Logout works and redirects to login
- [ ] Unauthenticated access to `/dashboard/` redirects to login
- [ ] `GET /api/me/` returns current user when logged in

## Dashboard

- [ ] Dashboard loads at `/dashboard/`
- [ ] Tenant name displayed correctly
- [ ] Navigation sidebar shows all modules

## Demo Center (Phase 13)

- [ ] Demo Center loads at `/demo/`
- [ ] Shows 10 active agent brains and mock mode status
- [ ] Shows 60 demo scenarios and quality audit target
- [ ] Agent scenario table links to playgrounds
- [ ] `docs/LOCAL_DEMO_GUIDE.md` exists

## Agents

- [ ] Agent catalog shows 10 template cards at `/agents/`
- [ ] All 10 agents show "Brain Active" badge
- [ ] Template detail page loads
- [ ] Deploy Sales Agent creates new instance
- [ ] Agent settings page loads and saves changes
- [ ] `GET /api/agent-templates/` returns 10 templates
- [ ] `GET /api/agents/` returns deployed instances

## Agent Playground (Phase 13)

- [ ] Playground loads scenario dropdown per agent
- [ ] Load scenario fills customer message
- [ ] Send shows normalized intent, raw intent (if different), and quality checks
- [ ] PASS / ACCEPTED / WARN / FAIL status displayed clearly
- [ ] WhatsApp mock and Instagram mock channels work

## Agent Quality (Phase 14)

- [ ] `python scripts/audit_agent_quality.py` reports 60 passed, 0 warnings, 0 failed
- [ ] `/settings/ai-providers/` shows provider status (no raw keys)
- [ ] `/settings/ai-providers/test/` runs mock provider test
- [ ] `GET /api/agent-engine/providers/status/` returns safe config
- [ ] Missing real provider key falls back to mock
- [ ] Analytics shows token/cost/fallback metrics

## Deploy Sales Agent

- [ ] Deploy from template creates active instance
- [ ] Settings editor saves business name, services, pricing
- [ ] Agent test message API returns reply
- [ ] `POST /api/agent-engine/test-message/` works with mock provider

## CRM

- [ ] Leads list loads at `/crm/leads/`
- [ ] Contacts list loads at `/crm/contacts/`
- [ ] Pipeline board loads at `/crm/pipeline/`
- [ ] Create new lead via UI or API
- [ ] Update lead status
- [ ] Create task linked to lead
- [ ] Demo seed shows 5 sample leads

## Inbox

- [ ] Inbox list loads at `/inbox/`
- [ ] Conversation detail shows message thread
- [ ] Staff can send reply
- [ ] Human takeover button works
- [ ] Re-enable AI button works
- [ ] Demo conversations visible from seed data

## Web Chat

- [ ] Web chat demo page loads at `/inbox/webchat/`
- [ ] Send customer message receives AI reply
- [ ] Conversation created in inbox
- [ ] `POST /api/webchat/message/` returns JSON reply

## Knowledge

- [ ] Knowledge list loads at `/knowledge/`
- [ ] Add new source creates chunks
- [ ] Source detail shows chunks
- [ ] Agent test message uses knowledge snippets
- [ ] Demo seed shows 5 knowledge sources

## Analytics

- [ ] Analytics dashboard loads at `/analytics/`
- [ ] KPI cards show non-zero values (after seed)
- [ ] Funnel chart displays lead statuses
- [ ] Date filter changes metrics
- [ ] `GET /api/analytics/overview/` returns JSON

## WhatsApp Mock Webhook

- [ ] `GET /api/webhooks/whatsapp/?hub.mode=subscribe&hub.verify_token=ai-agent-os-verify&hub.challenge=test123` returns `test123`
- [ ] POST mock WhatsApp payload creates conversation/message
- [ ] Webhook event logged at `/integrations/`
- [ ] Invalid verify token returns 403

## Instagram Mock Webhook

- [ ] `GET /api/webhooks/instagram/?hub.mode=subscribe&hub.verify_token=ai-agent-os-verify&hub.challenge=test456` returns `test456`
- [ ] POST mock Instagram payload processes message
- [ ] Webhook event appears in event log

## Human Handoff

- [ ] Message with complaint/refund intent triggers handoff
- [ ] Conversation `human_takeover` flag set to True
- [ ] AI stops replying after handoff
- [ ] Staff can reply manually

## Lead Scoring

- [ ] Agent extracts budget/timeline from message
- [ ] Lead score updates after agent interaction
- [ ] Score visible on lead detail page

## Hot Lead Detection

- [ ] High score (>= 70) sets lead status to `hot`
- [ ] Hot leads visible in CRM and analytics
- [ ] Follow-up task created for hot leads

## Tenant Scoping

- [ ] User A cannot see User B tenant data via API
- [ ] All list endpoints return only current tenant records
- [ ] Create second tenant + user and verify isolation

## API Smoke Tests

- [ ] `POST /api/auth/login/` — 200
- [ ] `GET /api/me/` — 200
- [ ] `GET /api/leads/` — 200
- [ ] `GET /api/conversations/` — 200
- [ ] `GET /api/knowledge/` — 200
- [ ] `GET /api/analytics/overview/` — 200
- [ ] `GET /api/integrations/channel-accounts/` — 200

## Environment / Deploy

- [ ] `python manage.py check` passes
- [ ] `python scripts/check_environment.py` runs without FAIL
- [ ] `python -m pytest tests/ -q` all pass
- [ ] `python scripts/smoke_test.py` passes

---

**Tester:** _______________  
**Date:** _______________  
**Environment:** local / Docker / staging  
**Overall result:** PASS / FAIL
