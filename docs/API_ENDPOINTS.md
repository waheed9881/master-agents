# API Endpoints

Base URL: `http://localhost:8000` (local) or your deployment domain.

Authentication: Session auth (browser) or POST `/api/auth/login/` for API clients.

All endpoints except login and webhooks require authentication. Data is tenant-scoped.

---

## Auth

### POST /api/auth/login/

Login and create session.

**Request:**
```json
{
  "email": "admin@example.com",
  "password": "Admin123!"
}
```

**Response (200):**
```json
{
  "id": 1,
  "email": "admin@example.com",
  "full_name": "Demo Admin",
  "role": "owner",
  "tenant": {"id": 1, "name": "Demo Company", "slug": "demo-company"}
}
```

### POST /api/auth/logout/

End session. Returns 200.

### GET /api/me/

Current authenticated user and tenant.

**Response (200):**
```json
{
  "id": 1,
  "email": "admin@example.com",
  "full_name": "Demo Admin",
  "role": "owner",
  "tenant": {"id": 1, "name": "Demo Company"}
}
```

---

## Agents

### GET /api/agent-templates/

List all active agent templates.

### GET /api/agent-templates/{id}/

Template detail including workflow and prompt defaults.

### GET /api/agents/

List tenant agent instances.

### POST /api/agents/

Deploy agent from template.

**Request:**
```json
{
  "template_id": 1,
  "name": "My Sales Agent",
  "language": "en",
  "tone": "professional"
}
```

### GET /api/agents/{id}/

Agent instance detail with settings.

### PATCH /api/agents/{id}/settings/

Update agent business settings.

**Request:**
```json
{
  "business_name": "Acme Corp",
  "business_description": "We sell widgets",
  "services_json": ["Consulting", "Support"],
  "pricing_json": {"starter": 99}
}
```

---

## CRM

### GET /api/contacts/

List tenant contacts. Supports search query param.

### POST /api/contacts/

Create contact.

**Request:**
```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "phone": "+1234567890",
  "source": "web"
}
```

### GET /api/leads/

List leads. Filter by `status` query param.

### POST /api/leads/

Create lead.

**Request:**
```json
{
  "contact_id": 1,
  "title": "Enterprise inquiry",
  "status": "new",
  "source": "web_chat"
}
```

### GET /api/leads/{id}/

Lead detail.

### PATCH /api/leads/{id}/

Update lead status, score, summary, etc.

### GET /api/pipeline/

Pipeline stages and deals board data.

### POST /api/tasks/

Create follow-up task.

**Request:**
```json
{
  "lead_id": 1,
  "title": "Call back tomorrow",
  "due_at": "2026-06-10T10:00:00Z"
}
```

---

## Inbox

### GET /api/conversations/

List conversations. Filter by `channel_type`, `status`.

### GET /api/conversations/{id}/

Conversation with messages.

### POST /api/conversations/{id}/messages/

Staff reply.

**Request:**
```json
{
  "message_text": "Thanks for reaching out. How can I help?"
}
```

### POST /api/conversations/{id}/human-takeover/

Enable human takeover (disables AI).

### POST /api/conversations/{id}/enable-ai/

Re-enable AI on conversation.

---

## Web Chat

### POST /api/webchat/message/

Customer message (no staff auth; uses session_key).

**Request:**
```json
{
  "message_text": "Hi, I want pricing info",
  "session_key": "abc-123",
  "agent_instance_id": 1
}
```

**Response (200):**
```json
{
  "reply": "Hello! I'd be happy to share our pricing...",
  "conversation_id": 5,
  "handoff": false
}
```

---

## Agent Engine

### POST /api/agent-engine/test-message/

Test agent with a message (staff auth required).

**Request:**
```json
{
  "agent_instance_id": 1,
  "message_text": "What are your prices?"
}
```

**Response (200):**
```json
{
  "reply": "...",
  "intent": "pricing",
  "confidence": 0.85,
  "handoff": false,
  "knowledge_used": ["Pricing Plans"]
}
```

---

## Knowledge

### GET /api/knowledge/

List knowledge sources for tenant.

### POST /api/knowledge/

Create knowledge source (auto-chunks content).

**Request:**
```json
{
  "title": "FAQ",
  "content": "Q: What is your refund policy?\nA: 30 days.",
  "source_type": "faq"
}
```

### POST /api/knowledge/upload/

Upload text file as knowledge source (multipart form).

---

## Analytics

All analytics endpoints accept optional `?days=30` query param.

### GET /api/analytics/overview/

KPI summary: leads, conversations, agent runs, hot leads.

### GET /api/analytics/funnel/

Lead conversion funnel by status.

### GET /api/analytics/agents/

Per-agent performance metrics.

### GET /api/analytics/inbox/

Inbox volume by channel and status.

### GET /api/analytics/knowledge/

Knowledge source and chunk counts.

### GET /api/analytics/recent-activity/

Recent leads, conversations, agent runs.

---

## Integrations

### GET /api/integrations/channel-accounts/

List channel accounts for tenant.

### GET /api/integrations/webhook-events/

List webhook event log. Filter by `channel_type`, `processing_status`.

---

## Webhooks

### GET /api/webhooks/whatsapp/

Meta webhook verification.

**Query params:** `hub.mode`, `hub.verify_token`, `hub.challenge`

Returns challenge string on success, 403 on failure.

### POST /api/webhooks/whatsapp/

Inbound WhatsApp messages. Requires `X-Hub-Signature-256` when mock mode is disabled.

### GET /api/webhooks/instagram/

Instagram webhook verification (same params as WhatsApp).

### POST /api/webhooks/instagram/

Inbound Instagram messages.

**Mock test payload (POST):**
```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "id": "WABA_ID",
    "changes": [{
      "value": {
        "messaging_product": "whatsapp",
        "metadata": {"phone_number_id": "demo-phone-id"},
        "messages": [{
          "id": "wamid.test123",
          "from": "15551234567",
          "timestamp": "1710000000",
          "type": "text",
          "text": {"body": "Hello"}
        }]
      },
      "field": "messages"
    }]
  }]
}
```
