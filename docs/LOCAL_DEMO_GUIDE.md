# Local Demo Guide — AI Agent OS

This guide covers running a polished local demo of AI Agent OS (Phase 13). Everything runs in **mock mode** — no external APIs or Meta credentials required.

## Prerequisites

- Python 3.12+
- PostgreSQL and Redis running locally (or Docker Compose)
- Dependencies installed: `pip install -r requirements.txt`

## Start the App

```bash
cp .env.example .env
python manage.py migrate
python scripts/seed_demo_data.py
python manage.py runserver
```

Open: http://localhost:8000/login/

**Demo login:**
- Email: `admin@example.com`
- Password: `Admin123!`

## Key Pages

| Page | URL | Purpose |
|------|-----|---------|
| Demo Center | `/demo/` | Control room, checklist, scenario table |
| Dashboard | `/dashboard/` | Workspace overview |
| Agents | `/agents/` | 10 agent templates (Brain Active) |
| Agent Playground | `/agents/instances/{id}/playground/` | Scenario-based testing |
| Integrations | `/integrations/` | Channel config (mock mode) |
| Webhook Events | `/integrations/webhook-events/` | Event audit log |
| Inbox | `/inbox/` | Conversations |
| CRM | `/crm/leads/` | Leads and pipeline |
| Knowledge | `/knowledge/` | Knowledge sources |
| Analytics | `/analytics/` | Metrics dashboard |

## 15-Minute Demo Script

1. **Login** — use demo credentials above.
2. **Demo Center** (`/demo/`) — show product status: 10 agents, mock AI, mock integrations.
3. **Agents gallery** — all 10 cards show "Brain Active".
4. **Sales Agent playground** — load "Pricing inquiry" scenario, send via web chat.
5. **Show results** — intent, reply, quality checks (pass/warn).
6. **CRM** — open new lead with score and status.
7. **Inbox** — show customer + AI message thread.
8. **Integrations** — run WhatsApp mock test on demo channel.
9. **Analytics** — show conversation and activity metrics.

## 30-Minute Demo Script

Follow the 15-minute script, then:

10. **Real Estate Agent** — load "Budget and location shared" scenario.
11. **Clinic Agent** — show "Urgent symptoms handoff" (safety escalation).
12. **eCommerce Agent** — show refund request handoff (no guaranteed refund).
13. **Finance Agent** — show tax advice handoff.
14. **Knowledge base** — show per-agent knowledge sources.
15. **Webhook Events** — show simulated event log.
16. **Agent quality audit** — run `python scripts/audit_agent_quality.py` (optional live).

## Sample Messages by Agent

### Sales Closing Agent
- "How much does WhatsApp automation cost? Budget $500/month."
- "Can I schedule a demo next Tuesday?"
- "I want to speak with a human please."

### Real Estate Agent
- "Looking for a 3 bedroom apartment downtown, budget $350k."
- "Can I schedule a property visit this weekend?"
- "I need help with legal paperwork for the contract."

### Clinic Agent
- "I need a dental appointment next Monday."
- "I have severe chest pain and cannot breathe." (urgent handoff)

### Home Services Agent
- "Plumbing leak, urgent! Water flooding basement."
- "Quote for kitchen renovation, budget $15,000."

### School Admin Agent
- "Enrollment inquiry for grade 5."
- "Serious complaint about bullying." (handoff)

### Voice Receptionist Agent
- "What are your business hours?"
- "Please call me back at +1-555-0199."

### Tender Proposal Agent
- "Help preparing proposal for government RFP, deadline March 30."
- "Need final pricing approval and legal compliance sign-off."

### eCommerce Support Agent
- "Where is order ORD-99887?"
- "I want a refund, product is damaged!" (handoff)

### Recruitment Agent
- "Applying for senior developer role, 5 years Python."
- "Want to negotiate salary and offer letter."

### Finance Assistant Agent
- "Question about invoice INV-2024-042."
- "I need tax advice on corporate filing." (handoff)

## Testing WhatsApp Mock

1. Go to **Integrations** (`/integrations/`).
2. Select WhatsApp demo channel → **Test webhook**.
3. Choose agent, enter customer message, send.
4. Check **Inbox** for WhatsApp conversation.
5. Check **Webhook Events** for processed event.

## Testing Instagram Mock

Same as WhatsApp, using Instagram demo channel or Agent Playground with **Instagram (Mock)** channel.

## Agent Playground Scenarios

Each agent has 5+ preset scenarios in the playground dropdown:

1. Select agent instance → **Test agent (Playground)**.
2. Choose scenario from dropdown → **Load scenario**.
3. Select channel (web chat / WhatsApp mock / Instagram mock).
4. Click **Send message**.
5. Compare **Expected behavior** vs **Actual result** panels.

## Quality Audit

```bash
python scripts/audit_agent_quality.py
```

Runs all **60 demo scenarios** against deployed agents in mock mode.

| Status | Meaning |
|--------|---------|
| **PASS** | All checks passed including normalized intent match |
| **ACCEPTED** | Intent matched via alias or handoff/safety correct despite label variance |
| **WARN** | Non-blocking issue (e.g. missing signal, intent mismatch without handoff) |
| **FAIL** | Blocking issue (no reply, wrong handoff, unsafe response, missing CRM) |

Target result: `60 passed, 0 warnings, 0 failed`.

Intents are normalized via `apps/agent_engine/intent_normalizer.py` before comparison. The mock provider uses rule-based keyword detection — not a live LLM.

### Testing real providers locally

1. Add API key to `.env` (e.g. `OPENAI_API_KEY=sk-...`)
2. Set `AI_PROVIDER=openai` (or groq/gemini)
3. Restart the server
4. Open `/settings/ai-providers/` to verify key status
5. Use `/settings/ai-providers/test/` for an isolated test
6. Keep `AI_FALLBACK_PROVIDER=mock` for safe fallback

Scenario audit always uses mock unless `AUDIT_AI_PROVIDER=env` is set.

## What Is Real vs Mock

| Feature | Local demo | Production |
|---------|------------|------------|
| AI replies | MockAIProvider (rule-based) | OpenAI/Groq/Gemini |
| WhatsApp/Instagram | Mock/simulator | Meta Graph API |
| Webhook signatures | Skipped in mock mode | HMAC validated |
| Credentials | Optional placeholders | Encrypted real tokens |

## What NOT to Claim in Demo

- Do **not** claim live WhatsApp or Instagram sending unless `INTEGRATIONS_MOCK_MODE=False` with real Meta setup.
- Do **not** claim AI provides medical diagnosis, tax advice, legal advice, or guaranteed refunds.
- Do **not** claim appointments or deals are final — staff confirmation is required.
- Do **not** claim live LLM intelligence — mock provider uses deterministic keyword matching with intent normalization.

## Validation Commands

```bash
python manage.py check
python scripts/check_environment.py
python scripts/smoke_test.py
python scripts/audit_routes.py
python scripts/api_smoke_test.py
python scripts/audit_agent_quality.py
python -m pytest tests/ -q
```
