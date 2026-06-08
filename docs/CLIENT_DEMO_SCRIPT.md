# Client Demo Script

Step-by-step scripts for presenting AI Agent OS locally. All URLs assume `http://127.0.0.1:8000`.

**Login:** `admin@example.com` / `Admin123!` (change before external demo)

---

## Before you start

1. Run `run_local_demo.bat` or `run_local_demo.ps1`
2. Open Demo Report: `/demo/report/` (optional print/PDF)
3. Confirm mock badges in top bar: **Mock AI**, **Mock Meta**, **Local**

---

## 15-minute demo

| Min | Step | URL | What to say |
|-----|------|-----|-------------|
| 0-2 | Dashboard | `/dashboard/` | Executive overview: agents, leads, conversations, security status |
| 2-4 | Agent gallery | `/agents/` | 10 templates, all Brain Active, grouped by vertical |
| 4-7 | Playground | `/agents/<id>/playground/` | Load **Pricing inquiry** scenario, send via web chat |
| 7-9 | CRM | `/crm/leads/` | Show new lead auto-created with score and status |
| 9-11 | Inbox | `/inbox/` | Show AI reply thread and human handoff option |
| 11-13 | Integrations | `/integrations/` | Run WhatsApp mock test message |
| 13-15 | Analytics | `/analytics/` | KPIs, agent runs, token/cost tracking |

### Sample playground message

```
Hello, I need pricing for your WhatsApp automation package for a team of 5.
```

### Expected results

- Playground returns structured reply with intent (e.g. pricing)
- CRM shows new or updated lead
- Inbox shows conversation with AI message
- Integration test creates webhook event

---

## 30-minute demo

Complete the 15-minute flow, then add:

| Min | Step | URL | What to say |
|-----|------|-----|-------------|
| 15-18 | Knowledge | `/knowledge/` | Agents answer from FAQs and pricing sources |
| 18-21 | Second agent | `/agents/` | Open clinic or real estate playground |
| 21-24 | Settings | `/settings/` | Workspace, team roles, plan limits |
| 24-27 | Security | `/settings/security/` | Encryption, rate limits, audit trail |
| 27-30 | Demo Center | `/demo/` | Quality score 60/60, mock vs real explanation |

### Second agent sample (clinic)

```
I need to book an appointment for a dental cleaning next week.
```

---

## What to say

- Multi-tenant SaaS with 10 vertical AI agents
- CRM, inbox, knowledge, and analytics are production-pattern modules
- Mock AI gives deterministic demo-safe responses
- Security hardening: encryption, rate limits, audit logs (Phase 16)
- 287 automated tests, 60/60 scenario QA pass

## What NOT to claim

- Do not say "live ChatGPT" unless `AI_PROVIDER` is set to openai/groq/gemini with API key
- Do not say "live WhatsApp" unless `INTEGRATIONS_MOCK_MODE=False` and Meta configured
- Do not say "payment billing works" — plan switching is local demo only
- Do not say "production deployed" — this is a local secure MVP

---

## Troubleshooting during demo

| Issue | Fix |
|-------|-----|
| Login fails | `python scripts/seed_demo_data.py` resets password to Admin123! |
| No agents | Run seed script; check `/agents/` shows 10 templates |
| Playground error | Confirm agent is deployed and mock AI is enabled |
| Empty CRM/inbox | Run playground or web chat first to generate data |
| 429 rate limit | Wait 60s or set `RATE_LIMITING_ENABLED=False` in `.env` |

---

## Print handout

Open `/demo/report/` and use **Print / Save as PDF** for a one-page summary.
