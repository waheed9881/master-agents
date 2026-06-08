# Architecture

## Modular Monolith

AI Agent OS uses a **modular monolith** pattern: one Django deployment with clearly bounded apps that can later be extracted into microservices.

```
config/                 # Settings, URLs, Celery, ASGI
apps/
  accounts/             # Users, auth, tenant middleware
  tenants/              # Workspaces, dashboard
  agents/               # Templates and instances
  crm/                  # Contacts, leads, pipeline
  inbox/                # Conversations, messages, channels
  integrations/         # Webhooks, Meta adapters
  knowledge/            # Sources and chunks
  agent_engine/         # Shared AI orchestration
  agent_modules/        # Per-agent business logic
  analytics/            # Read-only reporting selectors
templates/              # Server-rendered UI (HTMX + Alpine + Tailwind)
scripts/                # Seed and utility scripts
```

## Shared Core Apps

| App | Responsibility |
|-----|----------------|
| `accounts` | Custom user model, login, API auth, tenant middleware |
| `tenants` | Multi-tenant workspace, dashboard |
| `agents` | Template catalog, instance deployment, settings |
| `inbox` | Channel accounts, conversations, messages |
| `agent_engine` | Provider abstraction, orchestration, run logging |
| `knowledge` | Content storage, chunking, search |

Business modules (`crm`, `analytics`, `integrations`) plug into the core via Django imports and shared tenant scoping.

## Agent Modules

Each agent type lives under `apps/agent_modules/<module>/`:

- `sales_agent/` — fully implemented `SalesClosingAgent`
- Other 9 modules — stub packages registered in `AGENT_MODULE_MAP`

The orchestrator (`AgentOrchestrator`) maps `template.slug` to agent class via `AGENT_CLASS_MAP`. Only `sales-closing-agent` is registered today.

## Request Flow (Staff UI)

```
Browser -> Django URL -> View -> Template
                      -> TenantMiddleware (sets request.tenant)
                      -> LoginRequiredMixin / DRF IsAuthenticated
```

All staff views and APIs are tenant-scoped via `request.user.tenant`.

## Web Chat Flow

```
Customer widget POST /api/webchat/message/
  -> WebChatMessageAPIView
  -> InboundMessageService (create/find conversation)
  -> AgentOrchestrator.process_inbound_message()
  -> SalesClosingAgent.run()
  -> CRM update, knowledge search, handoff check
  -> Outbound reply stored as Message (sender_type=ai)
  -> JSON response to widget
```

## WhatsApp / Instagram Flow

```
Meta POST /api/webhooks/whatsapp/ or /api/webhooks/instagram/
  -> WebhookProcessorService
  -> Signature validation (skipped in mock mode)
  -> Idempotency check (external_message_id)
  -> Normalize payload to common format
  -> Resolve tenant via phone_number_id / page_id
  -> InboundMessageService + AgentOrchestrator
  -> OutboundMessageService (mock or live)
  -> WebhookEvent logged
```

GET requests handle Meta webhook verification (`hub.verify_token`, `hub.challenge`).

## AI Provider Layer

```
get_ai_provider() -> MockProvider | OpenAIProvider | GroqProvider | GeminiProvider
```

All live providers fall back to `MockProvider` if API key is missing or call fails.

## Future Extraction Path

| Current module | Future service |
|----------------|----------------|
| `agent_engine` + `agent_modules` | Agent Runtime Service |
| `inbox` + `integrations` | Channel Gateway Service |
| `knowledge` | Knowledge Service (with vector DB) |
| `crm` | CRM Service or external CRM sync |
| `analytics` | Analytics / BI pipeline |

Tenant ID would become the cross-service correlation key. Webhooks and internal APIs already use normalized message formats to ease extraction.
