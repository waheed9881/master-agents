# Database Schema

PostgreSQL database. All tenant-owned records include a `tenant_id` foreign key unless noted.

## Tenant

**Table:** `tenants_tenant`

| Field | Type | Notes |
|-------|------|-------|
| id | PK | |
| name | string | Display name |
| slug | string | Unique, URL-safe |
| country | string | |
| industry | string | |
| timezone | string | Default UTC |
| default_currency | string | Default USD |
| created_at, updated_at | datetime | |

## User

**Table:** `accounts_user`

| Field | Type | Notes |
|-------|------|-------|
| id | PK | |
| email | string | Unique, login field |
| full_name | string | |
| role | enum | owner, admin, sales_manager, sales_rep |
| tenant_id | FK | Nullable for superusers |
| is_active, is_staff, is_superuser | bool | |
| password | hashed | |
| created_at, updated_at | datetime | |

## AgentTemplate

**Table:** `agents_agenttemplate`

| Field | Type | Notes |
|-------|------|-------|
| id | PK | |
| name, slug | string | slug unique |
| description | text | |
| category, priority_label | string | |
| market_need_score | int | |
| tags_json | JSON | |
| default_workflow_json | JSON | |
| default_prompt | text | |
| is_active, is_implemented | bool | |
| created_at, updated_at | datetime | |

## AgentInstance

**Table:** `agents_agentinstance`

| Field | Type | Notes |
|-------|------|-------|
| id | PK | |
| tenant_id | FK | |
| template_id | FK | PROTECT |
| name | string | Unique per tenant+template |
| status | enum | draft, active, paused, archived |
| language, tone | string | |
| ai_enabled | bool | |
| created_at, updated_at | datetime | |

## AgentSettings

**Table:** `agents_agentsettings`

| Field | Type | Notes |
|-------|------|-------|
| id | PK | |
| agent_instance_id | FK | OneToOne |
| business_name, business_description | string/text | |
| services_json | JSON | |
| pricing_json | JSON | |
| qualification_questions_json | JSON | |
| objection_handling_json | JSON | |
| handoff_rules_json | JSON | |
| working_hours_json | JSON | |
| created_at, updated_at | datetime | |

## Contact

**Table:** `crm_contact`

| Field | Type | Notes |
|-------|------|-------|
| id | PK | |
| tenant_id | FK | |
| name, phone, email | string | |
| city, country, source | string | |
| metadata_json | JSON | |
| created_at, updated_at | datetime | |

## Lead

**Table:** `crm_lead`

| Field | Type | Notes |
|-------|------|-------|
| id | PK | |
| tenant_id | FK | |
| contact_id | FK | |
| agent_instance_id | FK | Nullable |
| title | string | |
| status | enum | new, qualifying, qualified, hot, demo_booked, won, lost |
| score | int | 0-100 |
| budget, need, timeline, source, summary | string/text | |
| next_follow_up_at | datetime | Nullable |
| created_at, updated_at | datetime | |

## PipelineStage

**Table:** `crm_pipelinestage`

| Field | Type | Notes |
|-------|------|-------|
| id | PK | |
| tenant_id | FK | |
| name | string | Unique per tenant |
| order | int | |
| is_default | bool | |
| created_at, updated_at | datetime | |

Default stages: New, Qualifying, Qualified, Proposal, Negotiation, Won, Lost.

## Deal

**Table:** `crm_deal`

| Field | Type | Notes |
|-------|------|-------|
| id | PK | |
| tenant_id | FK | |
| lead_id | FK | |
| pipeline_stage_id | FK | PROTECT |
| value | decimal | |
| currency | string | |
| probability | int | |
| expected_close_date | date | Nullable |
| created_at, updated_at | datetime | |

## Task

**Table:** `crm_task`

| Field | Type | Notes |
|-------|------|-------|
| id | PK | |
| tenant_id | FK | |
| lead_id | FK | Nullable |
| assigned_to_id | FK User | Nullable |
| title, description | string/text | |
| due_at | datetime | Nullable |
| status | enum | open, in_progress, done, cancelled |
| created_at, updated_at | datetime | |

## ChannelAccount

**Table:** `inbox_channelaccount`

| Field | Type | Notes |
|-------|------|-------|
| id | PK | |
| tenant_id | FK | |
| channel_type | enum | web_chat, whatsapp, instagram |
| display_name | string | |
| credentials_encrypted | text | Placeholder |
| is_active | bool | |
| created_at, updated_at | datetime | |

## Conversation

**Table:** `inbox_conversation`

| Field | Type | Notes |
|-------|------|-------|
| id | PK | |
| tenant_id | FK | |
| contact_id | FK | |
| agent_instance_id | FK | Nullable |
| channel_type | enum | |
| status | enum | open, closed, archived |
| ai_enabled, human_takeover | bool | |
| session_key | string | Web chat session |
| last_message_at | datetime | |
| created_at, updated_at | datetime | |

## Message

**Table:** `inbox_message`

| Field | Type | Notes |
|-------|------|-------|
| id | PK | |
| conversation_id | FK | |
| sender_type | enum | customer, ai, human, system |
| message_text | text | |
| metadata_json | JSON | |
| created_at | datetime | |

## AgentRun

**Table:** `agent_engine_agentrun`

| Field | Type | Notes |
|-------|------|-------|
| id | PK | |
| tenant_id | FK | |
| agent_instance_id | FK | |
| conversation_id | FK | Nullable |
| input_message, output_message | text | |
| intent | string | |
| confidence | float | |
| tokens_used | int | |
| cost_estimate | decimal | |
| created_at | datetime | |

## ToolCall

**Table:** `agent_engine_toolcall`

| Field | Type | Notes |
|-------|------|-------|
| id | PK | |
| agent_run_id | FK | |
| tool_name | string | e.g. knowledge_search, update_crm |
| input_json, output_json | JSON | |
| status | enum | success, failed, skipped |
| created_at | datetime | |

## KnowledgeSource

**Table:** `knowledge_knowledgesource`

| Field | Type | Notes |
|-------|------|-------|
| id | PK | |
| tenant_id | FK | |
| agent_instance_id | FK | Nullable (tenant-wide if null) |
| source_type | enum | text, faq, pricing, policy, upload, url |
| title | string | |
| content | text | |
| created_at, updated_at | datetime | |

## KnowledgeChunk

**Table:** `knowledge_knowledgechunk`

| Field | Type | Notes |
|-------|------|-------|
| id | PK | |
| tenant_id | FK | |
| source_id | FK | |
| chunk_text | text | |
| embedding | JSON | pgvector-ready placeholder |
| metadata_json | JSON | |
| created_at, updated_at | datetime | |

## WebhookEvent

**Table:** `integrations_webhookevent`

| Field | Type | Notes |
|-------|------|-------|
| id | PK | |
| tenant_id | FK | Nullable |
| channel_type | string | whatsapp, instagram |
| external_event_id, external_message_id | string | Idempotency |
| event_type | string | |
| payload_json, normalized_json | JSON | |
| processing_status | enum | received, ignored, processed, failed, duplicate |
| error_message | text | |
| received_at, processed_at, created_at | datetime | |

## ChannelCredential

**Table:** `integrations_channelcredential`

| Field | Type | Notes |
|-------|------|-------|
| id | PK | |
| tenant_id | FK | |
| channel_account_id | FK | OneToOne |
| provider | string | Default meta |
| app_id, page_id, business_account_id, phone_number_id | string | |
| access_token_encrypted, app_secret_encrypted | text | Placeholder encryption |
| verify_token | string | |
| is_active | bool | |
| created_at, updated_at | datetime | |

## Entity Relationships (Summary)

```
Tenant
  ├── Users
  ├── AgentInstances -> AgentTemplate, AgentSettings
  ├── Contacts -> Leads -> Deals, Tasks
  ├── ChannelAccounts -> ChannelCredential
  ├── Conversations -> Messages
  ├── AgentRuns -> ToolCalls
  ├── KnowledgeSources -> KnowledgeChunks
  └── WebhookEvents
```
