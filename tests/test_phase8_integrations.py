"""Phase 8 tests: WhatsApp and Instagram integration hardening."""
import json

import pytest
from django.test import override_settings

from apps.agent_engine.models import AgentRun
from apps.agents.models import AgentTemplate
from apps.agents.services import create_agent_instance, update_agent_settings
from apps.inbox.models import ChannelType, Conversation, Message
from apps.integrations.models import WebhookEvent, WebhookProcessingStatus
from apps.integrations.services.normalizers import (
    normalize_instagram_payload,
    normalize_whatsapp_payload,
)
from apps.integrations.services.outbound import OutboundMessageService
from apps.integrations.services.webhook_processor import WebhookProcessorService
from apps.tenants.services import create_tenant

VERIFY_TOKEN = "ai-agent-os-verify"
DEMO_PHONE = "demo_phone_number_id"
DEMO_PAGE = "demo_instagram_page_id"


def _whatsapp_payload(message_id="wamid.TEST123", text="Hello, what is pricing?"):
    return {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WABA_DEMO",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"phone_number_id": DEMO_PHONE},
                    "contacts": [{"wa_id": "15551234567", "profile": {"name": "John Demo"}}],
                    "messages": [{
                        "from": "15551234567",
                        "id": message_id,
                        "timestamp": "1700000000",
                        "type": "text",
                        "text": {"body": text},
                    }],
                },
            }],
        }],
    }


def _instagram_payload(message_id="mid.INST123", text="Hi from Instagram"):
    return {
        "object": "instagram",
        "entry": [{
            "id": DEMO_PAGE,
            "messaging": [{
                "sender": {"id": "ig_sender_123"},
                "recipient": {"id": DEMO_PAGE},
                "timestamp": 1700000000,
                "message": {"mid": message_id, "text": text},
            }],
        }],
    }


@pytest.fixture
def integrations_setup(client, db):
    from apps.accounts.models import User, UserRole
    from scripts.seed_integrations_demo import seed_integrations_for_tenant

    tenant = create_tenant(name="Integrations Co")
    User.objects.create_user(
        email="integrations@test.com",
        password="TestPass123!",
        full_name="Integrations Tester",
        tenant=tenant,
        role=UserRole.OWNER,
    )
    template = AgentTemplate.objects.create(
        name="Sales Closing Agent",
        slug="sales-closing-agent",
        description="Sales",
        category="Sales",
        is_implemented=True,
    )
    agent = create_agent_instance(tenant, template, status="active")
    update_agent_settings(agent, business_name="Integrations Co", pricing_json={"Starter": "$299/month"})
    seed_integrations_for_tenant(tenant)
    client.login(username="integrations@test.com", password="TestPass123!")
    return client, tenant, agent


@pytest.mark.django_db
class TestWebhookVerification:
    def test_whatsapp_verification_success(self, client):
        response = client.get(
            "/api/webhooks/whatsapp/",
            {"hub.mode": "subscribe", "hub.verify_token": VERIFY_TOKEN, "hub.challenge": "challenge123"},
        )
        assert response.status_code == 200
        assert response.content.decode() == "challenge123"

    def test_whatsapp_verification_failure(self, client):
        response = client.get(
            "/api/webhooks/whatsapp/",
            {"hub.mode": "subscribe", "hub.verify_token": "wrong-token", "hub.challenge": "x"},
        )
        assert response.status_code == 403

    def test_instagram_verification_success(self, client):
        response = client.get(
            "/api/webhooks/instagram/",
            {"hub.mode": "subscribe", "hub.verify_token": VERIFY_TOKEN, "hub.challenge": "ig_challenge"},
        )
        assert response.status_code == 200
        assert response.content.decode() == "ig_challenge"

    def test_instagram_verification_failure(self, client):
        response = client.get(
            "/api/webhooks/instagram/",
            {"hub.mode": "subscribe", "hub.verify_token": "bad", "hub.challenge": "x"},
        )
        assert response.status_code == 403


@pytest.mark.django_db
class TestNormalizers:
    def test_whatsapp_normalizes_text(self):
        results = normalize_whatsapp_payload(_whatsapp_payload())
        assert len(results) == 1
        msg = results[0]
        assert msg.channel_type == "whatsapp"
        assert msg.external_message_id == "wamid.TEST123"
        assert msg.sender_phone == "15551234567"
        assert "pricing" in msg.message_text

    def test_instagram_normalizes_text(self):
        results = normalize_instagram_payload(_instagram_payload())
        assert len(results) == 1
        msg = results[0]
        assert msg.channel_type == "instagram"
        assert msg.external_message_id == "mid.INST123"
        assert msg.message_text == "Hi from Instagram"


@pytest.mark.django_db
class TestInboundWebhooks:
    def test_whatsapp_creates_inbox_message(self, integrations_setup, client):
        _, tenant, _ = integrations_setup
        response = client.post(
            "/api/webhooks/whatsapp/",
            data=json.dumps(_whatsapp_payload()),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["processed"] == 1
        assert Conversation.objects.filter(tenant=tenant, channel_type=ChannelType.WHATSAPP).exists()
        assert Message.objects.filter(
            conversation__tenant=tenant,
            metadata_json__external_message_id="wamid.TEST123",
        ).exists()
        assert WebhookEvent.objects.filter(
            channel_type="whatsapp",
            processing_status=WebhookProcessingStatus.PROCESSED,
        ).exists()

    def test_instagram_creates_inbox_message(self, integrations_setup, client):
        _, tenant, _ = integrations_setup
        response = client.post(
            "/api/webhooks/instagram/",
            data=json.dumps(_instagram_payload()),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["processed"] == 1
        assert Conversation.objects.filter(tenant=tenant, channel_type=ChannelType.INSTAGRAM).exists()

    def test_duplicate_message_ignored(self, integrations_setup, client):
        client, _, _ = integrations_setup
        payload = _whatsapp_payload(message_id="wamid.DUPLICATE1")
        client.post("/api/webhooks/whatsapp/", data=json.dumps(payload), content_type="application/json")
        response = client.post(
            "/api/webhooks/whatsapp/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.json()["duplicates"] == 1
        assert Message.objects.filter(metadata_json__external_message_id="wamid.DUPLICATE1").count() == 1

    def test_invalid_payload_does_not_crash(self, client):
        response = client.post(
            "/api/webhooks/instagram/",
            {"object": "instagram"},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["status"] == "received"

    def test_sales_agent_runs_for_whatsapp(self, integrations_setup, client):
        _, tenant, _ = integrations_setup
        client.post(
            "/api/webhooks/whatsapp/",
            data=json.dumps(_whatsapp_payload(message_id="wamid.AGENT1", text="I need pricing ASAP")),
            content_type="application/json",
        )
        assert AgentRun.objects.filter(tenant=tenant).exists()
        assert Message.objects.filter(conversation__tenant=tenant, sender_type="ai").exists()


@pytest.mark.django_db
class TestOutbound:
    def test_mock_outbound_sender(self):
        result = OutboundMessageService.mock_send("whatsapp", "15551234567", "Test reply")
        assert result["success"] is True
        assert result["mock"] is True
        assert result["provider_message_id"].startswith("mock_whatsapp_")


@pytest.mark.django_db
class TestIntegrationsUI:
    def test_integrations_page_loads(self, integrations_setup):
        client, _, _ = integrations_setup
        response = client.get("/integrations/")
        assert response.status_code == 200
        assert b"WhatsApp Demo Channel" in response.content
        assert b"Mock mode" in response.content

    def test_channel_accounts_api(self, integrations_setup):
        client, _, _ = integrations_setup
        response = client.get("/api/integrations/channel-accounts/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        assert any(a["phone_number_id"] == DEMO_PHONE for a in data)


@pytest.mark.django_db
class TestSignatureValidation:
    @override_settings(INTEGRATIONS_MOCK_MODE=False, META_APP_SECRET="testsecret")
    def test_invalid_signature_rejected_when_enforced(self, client):
        response = client.post(
            "/api/webhooks/whatsapp/",
            data=json.dumps(_whatsapp_payload(message_id="wamid.SIG1")),
            content_type="application/json",
            HTTP_X_HUB_SIGNATURE_256="sha256=invalid",
        )
        assert response.status_code == 403
