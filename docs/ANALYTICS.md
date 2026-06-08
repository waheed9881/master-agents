# Analytics

## Overview

The analytics app (`apps/analytics/`) provides read-only reporting over existing data. It has no dedicated models; selectors query CRM, inbox, agent engine, and knowledge tables.

## Dashboard

**URL:** `/analytics/`

Sections:
- KPI overview cards
- Lead conversion funnel
- Agent performance table
- Inbox volume by channel
- Knowledge stats
- Recent activity feed

## Metrics

### Overview (`/api/analytics/overview/`)

| Metric | Source |
|--------|--------|
| Total leads | `crm.Lead` |
| Hot leads | Leads with status=hot |
| Open conversations | `inbox.Conversation` status=open |
| Agent runs | `agent_engine.AgentRun` |
| AI replies | Messages sender_type=ai |
| Knowledge sources | `knowledge.KnowledgeSource` |

### Funnel (`/api/analytics/funnel/`)

Lead counts grouped by status: new, qualifying, qualified, hot, demo_booked, won, lost.

### Agents (`/api/analytics/agents/`)

Per agent instance:
- Run count
- Average confidence
- Handoff count
- Leads created/updated

### Inbox (`/api/analytics/inbox/`)

- Conversations by channel (web_chat, whatsapp, instagram)
- Messages by sender type
- Human takeover count

### Knowledge (`/api/analytics/knowledge/`)

- Source count by type
- Total chunks
- Sources with zero chunks (data quality)

### Recent Activity (`/api/analytics/recent-activity/`)

Latest leads, conversations, and agent runs (last 10 each).

## Date Filters

All API endpoints accept `?days=N` (default 30). Filters on `created_at` or `last_message_at` depending on metric.

Example: `/api/analytics/overview/?days=7`

## APIs

| Method | Path | Purpose |
|--------|------|---------|
| GET | /api/analytics/overview/ | KPI summary |
| GET | /api/analytics/funnel/ | Lead funnel |
| GET | /api/analytics/agents/ | Agent metrics |
| GET | /api/analytics/inbox/ | Inbox metrics |
| GET | /api/analytics/knowledge/ | Knowledge stats |
| GET | /api/analytics/recent-activity/ | Activity feed |

## Tenant Scoping

All selectors filter by `request.user.tenant`. Cross-tenant data is never returned.

**File:** `apps/analytics/selectors.py`

## Dashboard Sections (UI)

1. **Header** — date range selector (7/30/90 days via HTMX)
2. **KPI row** — 6 metric cards
3. **Funnel chart** — horizontal progress bars per status
4. **Agent table** — sortable performance data
5. **Inbox breakdown** — channel and sender type counts
6. **Knowledge summary** — source/chunk counts
7. **Activity feed** — recent events list
