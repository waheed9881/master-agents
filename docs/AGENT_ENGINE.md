# Agent Engine

## Overview

The agent engine (`apps/agent_engine/`) provides shared AI orchestration for all agent types. Business logic for each agent lives in `apps/agent_modules/`.

## BaseAgent Interface

**File:** `apps/agent_engine/base.py`

Abstract class with `template_slug` and constructor `(agent_instance, provider?)`.

### Pipeline (`run` method)

1. **understand_message** — detect intent and confidence via AI provider
2. **search_knowledge** — retrieve relevant snippets
3. **build_prompt** — assemble system + user prompts
4. **generate_reply** — call AI provider
5. **extract_lead_data** — parse budget, timeline, contact info
6. **decide_handoff** — check handoff rules
7. **decide_next_action** — agent-specific action (abstract)
8. **update_crm** — agent-specific CRM updates (abstract)

Returns `AgentRunResult` with reply, intent, confidence, extracted lead data, handoff flags, and knowledge used.

## SalesClosingAgent Flow

**File:** `apps/agent_modules/sales_agent/agent.py`  
**Slug:** `sales-closing-agent`

### decide_next_action

Based on intent and extracted signals:

| Condition | Action |
|-----------|--------|
| Handoff triggered | handoff |
| Demo intent | book_demo |
| Pricing question | share_pricing |
| Enough qualification data | qualify |
| Otherwise | continue_qualifying |

### update_crm

- Updates contact fields (email, phone)
- Finds or creates lead linked to agent instance
- Applies lead scoring (budget, timeline, intent signals)
- Sets status to `hot` when score >= 70
- Creates follow-up tasks for hot leads
- Sets `demo_booked` when demo is scheduled

### run_with_handoff

Calls `run()` then `enable_human_takeover()` on conversation if handoff is required.

## AI Providers

**Factory:** `apps/agent_engine/providers/factory.py`

| Provider | Env var | Model | Fallback |
|----------|---------|-------|----------|
| mock | (default) | Rule-based | — |
| openai | OPENAI_API_KEY | gpt-4o-mini | mock |
| groq | GROQ_API_KEY | llama-3.1-8b-instant | mock |
| gemini | GEMINI_API_KEY | gemini-1.5-flash | mock |

Set `AI_PROVIDER=mock` for demos and CI.

### Provider settings UI

- `/settings/ai-providers/` — read-only env configuration status
- `/settings/ai-providers/test/` — isolated provider test form
- API: `GET /api/agent-engine/providers/status/`, `POST /api/agent-engine/providers/test/`

API keys are read from environment variables only — never stored in the database.

### Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| AI_PROVIDER | mock | Active provider |
| AI_MODEL_NAME | (provider default) | Override model |
| AI_MAX_TOKENS | 800 | Max completion tokens |
| AI_TEMPERATURE | 0.3 | Sampling temperature |
| AI_FALLBACK_PROVIDER | mock | Fallback when key missing or request fails |
| AI_DAILY_TOKEN_BUDGET | — | Placeholder budget cap |
| AI_MONTHLY_TOKEN_BUDGET | — | Placeholder budget cap |
| AUDIT_AI_PROVIDER | mock | Force provider for scenario audit |

### Structured output

**File:** `apps/agent_engine/structured_output.py`

All providers target a common JSON schema: `reply_text`, `intent`, `extracted_fields`, `handoff_required`, `safety_flags`, `confidence`, etc.

- Mock provider generates structured metadata directly
- Real providers receive JSON instructions in the system prompt
- Invalid JSON falls back to plain text + deterministic intent extractor

### Safety guardrails

**File:** `apps/agent_engine/services/safety_guardrails.py`

Post-processes replies to block unsafe overpromises, force handoff for sensitive categories (tax, urgent medical, refund guarantees), and rewrite unsafe replies.

### Fallback behavior

**File:** `apps/agent_engine/services/provider_health.py`

If a real provider key is missing or the HTTP request fails, the engine falls back to `MockAIProvider`. `AgentRun.fallback_used` and `metadata_json` record fallback details.

## Mock Provider

**File:** `apps/agent_engine/providers/mock.py`

Rule-based intent detection and canned replies. No external API calls. Suitable for:

- Local development
- CI tests
- Client demos without API keys

## PromptBuilder

**File:** `apps/agent_engine/services/prompt_builder.py`

### build_system_prompt

Includes: business name/description, services, pricing, tone, language, knowledge context, safety rules, qualification questions.

### Safety rules

- No guaranteed results
- No invented pricing
- No legal/medical/financial advice
- Disclose AI identity
- Clarify when information is missing
- Hand off for sensitive decisions

### build_user_prompt

Recent conversation messages (last 6), current customer message, contact name.

## KnowledgeSearchService

**File:** `apps/agent_engine/services/knowledge_search.py`

Two-tier search (default limit 5):

1. Agent settings keyword match on `business_description`, `services_json`, `pricing_json`
2. Knowledge chunks via `apps.knowledge.services.search_knowledge_for_agent`

`format_context()` joins results as bullet list for prompt injection.

## ToolRegistry

**File:** `apps/agent_engine/services/tool_registry.py`

Simple class-level registry (`register`, `get`, `list_tools`, `execute`). Defined for future extensibility; orchestrator currently writes `ToolCall` records directly.

Logged tools: `knowledge_search`, `update_crm`, `handoff`.

## Lead Scoring

Rule-based scoring in SalesClosingAgent CRM update:

- Budget mentioned: +20
- Timeline urgency: +15
- High-intent keywords: +10-25
- Contact info provided: +10
- Score >= 70 triggers `hot` status

## Human Handoff Rules

**File:** `apps/agent_engine/services/handoff_decision.py`

Triggers handoff when:

- Intent is `complaint`, `legal`, `refund`, or `human_request`
- Message contains angry/sensitive words
- AI confidence < 0.6
- Agent settings `handoff_rules_json` matched

Handoff sets `conversation.human_takeover = True` and `ai_enabled = False`.

## Orchestrator

**File:** `apps/agent_engine/services/orchestrator.py`

```python
AGENT_CLASS_MAP = {
    "sales-closing-agent": SalesClosingAgent,
}
```

`process_inbound_message()` resolves agent, runs pipeline, logs `AgentRun` and `ToolCall` records.

## Test API

`POST /api/agent-engine/test-message/` — send a test message to an agent without a live conversation.
