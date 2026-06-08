# Integrations

## Overview

The integrations app (`apps/integrations/`) handles WhatsApp and Instagram via Meta Cloud API webhooks, plus web chat (handled in inbox app).

## Web Chat

- Demo page: `/inbox/webchat-demo/`
- API: `POST /api/webchat/message/`
- No Meta credentials required
- Uses `session_key` to maintain conversation continuity

## WhatsApp Webhook Verification

**Endpoint:** `GET /api/webhooks/whatsapp/`

Meta sends:
- `hub.mode=subscribe`
- `hub.verify_token` — must match `META_VERIFY_TOKEN`
- `hub.challenge` — returned as plain text on success

**Default verify token:** `ai-agent-os-verify` (set in `.env`)

## Instagram Webhook Verification

**Endpoint:** `GET /api/webhooks/instagram/`

Same verification flow as WhatsApp.

## Mock Mode

Set `INTEGRATIONS_MOCK_MODE=True` (default) to:

- Skip `X-Hub-Signature-256` enforcement
- Use `OutboundMessageService` mock sender (logs instead of calling Meta API)
- Allow local webhook testing without Meta app credentials

Safe for demos, staging, and CI.

## Meta Environment Variables

| Variable | Purpose |
|----------|---------|
| META_VERIFY_TOKEN | Webhook subscription verification |
| META_APP_SECRET | HMAC signature validation |
| META_ACCESS_TOKEN | Outbound message API calls |
| WHATSAPP_PHONE_NUMBER_ID | Route inbound WhatsApp to tenant |
| INSTAGRAM_PAGE_ID | Route inbound Instagram to tenant |
| INTEGRATIONS_MOCK_MODE | Enable/disable mock behavior |

## Signature Validation

When `INTEGRATIONS_MOCK_MODE=False`:

1. Meta sends `X-Hub-Signature-256: sha256=<hex>`
2. `verify_meta_signature()` computes HMAC-SHA256 of raw body with `META_APP_SECRET`
3. Mismatch returns 403 Forbidden

**File:** `apps/integrations/services/channel_credentials.py`

## Idempotency

**File:** `apps/integrations/services/idempotency.py`

- Extracts `external_message_id` from normalized payload
- Checks `WebhookEvent` for duplicate `external_message_id`
- Duplicates are logged with status `duplicate` and skipped

## Outbound Mock Sender

**File:** `apps/integrations/services/outbound.py`

In mock mode, outbound replies are logged to console/WebhookEvent metadata instead of calling Meta Graph API.

## Webhook Processing Pipeline

```
POST webhook
  -> validate signature (skipped in mock mode)
  -> normalize payload (whatsapp.py / instagram.py normalizers)
  -> check idempotency
  -> resolve tenant (phone_number_id or page_id -> ChannelCredential)
  -> InboundMessageService.create_message()
  -> AgentOrchestrator.process_inbound_message()
  -> OutboundMessageService.send() (mock or live)
  -> WebhookEvent status updated
```

## Channel Credentials

`ChannelCredential` model stores per-tenant Meta credentials linked to `ChannelAccount`.

Demo seed creates credentials with:
- `verify_token`: `ai-agent-os-verify`
- Demo `phone_number_id` and `page_id`

## Live Meta Setup (Future)

To go live:

1. Create Meta Developer App with WhatsApp and/or Instagram products
2. Set `INTEGRATIONS_MOCK_MODE=False`
3. Configure `META_APP_SECRET`, `META_ACCESS_TOKEN`
4. Set `WHATSAPP_PHONE_NUMBER_ID` and/or `INSTAGRAM_PAGE_ID`
5. Point Meta webhook URL to `https://yourdomain.com/api/webhooks/whatsapp/`
6. Set `META_VERIFY_TOKEN` to match Meta app configuration
7. Add domain to `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`
8. Ensure HTTPS (Meta requires public HTTPS endpoint)
9. Store credentials in `ChannelCredential` per tenant (encryption recommended)

## Webhook Event Log

View events at `/integrations/` UI or `GET /api/integrations/webhook-events/`.

Statuses: `received`, `ignored`, `processed`, `failed`, `duplicate`.
