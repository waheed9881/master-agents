"""Phase 11 tests: integrations configuration UI and mock channels."""
import json

import pytest
from django.test import override_settings

from apps.accounts.models import User, UserRole
from apps.agents.models import AgentTemplate
from apps.agents.services import create_agent_instance, update_agent_settings
from apps.inbox.models import ChannelAccount, ChannelType, Conversation, Message
from apps.integrations.models import WebhookEvent
from apps.tenants.services import create_tenant

VERIFY_TOKEN = "ai-agent-os-verify"


@pytest.fixture
def phase11_integrations_setup(client, db):
    tenant = create_tenant(name="Phase11 Integrations Co")
    User.objects.create_user(
        email="phase11int@test.com",
        password="TestPass123!",
        full_name="Phase11 Tester",
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
    update_agent_settings(agent, business_name="Phase11 Co")
    client.login(username="phase11int@test.com", password="TestPass123!")
    return client, tenant, agent


@pytest.mark.django_db
class TestIntegrationsUI:
    def test_integrations_index_loads(self, phase11_integrations_setup):
        client, _, _ = phase11_integrations_setup
        response = client.get("/integrations/")
        assert response.status_code == 200
        assert b"Integrations" in response.content or b"Channels" in response.content

    def test_create_whatsapp_channel_ui(self, phase11_integrations_setup):
        client, tenant, _ = phase11_integrations_setup
        response = client.post(
            "/integrations/channels/new/",
            {
                "channel_type": ChannelType.WHATSAPP,
                "display_name": "Test WhatsApp",
                "phone_number_id": "test_phone_123",
                "verify_token": VERIFY_TOKEN,
                "is_active": "on",
                "mock_mode": "on",
            },
        )
        assert response.status_code == 302
        account = ChannelAccount.objects.get(tenant=tenant, display_name="Test WhatsApp")
        assert account.channel_type == ChannelType.WHATSAPP
        assert account.mock_mode is True

    def test_create_instagram_channel_ui(self, phase11_integrations_setup):
        client, tenant, _ = phase11_integrations_setup
        response = client.post(
            "/integrations/channels/new/",
            {
                "channel_type": ChannelType.INSTAGRAM,
                "display_name": "Test Instagram",
                "instagram_page_id": "test_page_456",
                "verify_token": VERIFY_TOKEN,
                "is_active": "on",
                "mock_mode": "on",
            },
        )
        assert response.status_code == 302
        account = ChannelAccount.objects.get(tenant=tenant, display_name="Test Instagram")
        assert account.channel_type == ChannelType.INSTAGRAM

    def test_edit_channel_ui(self, phase11_integrations_setup):
        client, tenant, _ = phase11_integrations_setup
        account = ChannelAccount.objects.create(
            tenant=tenant,
            channel_type=ChannelType.WHATSAPP,
            display_name="Editable WA",
            mock_mode=True,
        )
        response = client.post(
            f"/integrations/channels/{account.pk}/edit/",
            {
                "channel_type": ChannelType.WHATSAPP,
                "display_name": "Updated WA Name",
                "phone_number_id": "updated_phone",
                "mock_mode": "on",
                "is_active": "on",
            },
        )
        assert response.status_code == 302
        account.refresh_from_db()
        assert account.display_name == "Updated WA Name"

    def test_whatsapp_mock_test_routes_to_inbox(self, phase11_integrations_setup):
        client, tenant, agent = phase11_integrations_setup
        account = ChannelAccount.objects.create(
            tenant=tenant,
            channel_type=ChannelType.WHATSAPP,
            display_name="WA Test",
            mock_mode=True,
        )
        from apps.integrations.models import ChannelCredential

        ChannelCredential.objects.create(
            tenant=tenant,
            channel_account=account,
            phone_number_id="test_wa_phone",
            verify_token=VERIFY_TOKEN,
        )
        response = client.post(
            f"/integrations/channels/{account.pk}/test/",
            {
                "message_text": "Hello, I need pricing",
                "customer_name": "WA Tester",
                "customer_phone": "+15550001111",
                "agent_instance_id": agent.pk,
            },
        )
        assert response.status_code == 200
        assert Conversation.objects.filter(tenant=tenant, channel_type=ChannelType.WHATSAPP).exists()
        assert Message.objects.filter(conversation__tenant=tenant, sender_type="ai").exists()

    def test_instagram_mock_test_routes_to_inbox(self, phase11_integrations_setup):
        client, tenant, agent = phase11_integrations_setup
        account = ChannelAccount.objects.create(
            tenant=tenant,
            channel_type=ChannelType.INSTAGRAM,
            display_name="IG Test",
            mock_mode=True,
        )
        from apps.integrations.models import ChannelCredential

        ChannelCredential.objects.create(
            tenant=tenant,
            channel_account=account,
            page_id="test_ig_page",
            verify_token=VERIFY_TOKEN,
        )
        response = client.post(
            f"/integrations/channels/{account.pk}/test/",
            {
                "message_text": "Hi from Instagram",
                "customer_name": "IG Tester",
                "customer_username": "ig_user_test",
                "agent_instance_id": agent.pk,
            },
        )
        assert response.status_code == 200
        assert Conversation.objects.filter(tenant=tenant, channel_type=ChannelType.INSTAGRAM).exists()

    def test_webhook_events_page_visible(self, phase11_integrations_setup):
        client, tenant, _ = phase11_integrations_setup
        WebhookEvent.objects.create(
            tenant=tenant,
            channel_type=ChannelType.WHATSAPP,
            external_message_id="evt_test_1",
            processing_status="processed",
        )
        response = client.get("/integrations/webhook-events/")
        assert response.status_code == 200
        assert b"evt_test_1" in response.content

    def test_create_whatsapp_channel_api(self, phase11_integrations_setup):
        client, tenant, _ = phase11_integrations_setup
        response = client.post(
            "/api/integrations/channel-accounts/",
            data=json.dumps({
                "channel_type": ChannelType.WHATSAPP,
                "display_name": "API WhatsApp",
                "phone_number_id": "api_phone_id",
                "mock_mode": True,
                "is_active": True,
            }),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert ChannelAccount.objects.filter(tenant=tenant, display_name="API WhatsApp").exists()

    def test_mock_mode_does_not_require_credentials(self, phase11_integrations_setup):
        client, tenant, _ = phase11_integrations_setup
        response = client.post(
            "/integrations/channels/new/",
            {
                "channel_type": ChannelType.WHATSAPP,
                "display_name": "Mock Only WA",
                "mock_mode": "on",
                "is_active": "on",
            },
        )
        assert response.status_code == 302
        assert ChannelAccount.objects.filter(tenant=tenant, display_name="Mock Only WA").exists()

    @override_settings(INTEGRATIONS_MOCK_MODE=False)
    def test_live_mode_warns_missing_credentials(self, phase11_integrations_setup):
        client, _, _ = phase11_integrations_setup
        response = client.post(
            "/integrations/channels/new/",
            {
                "channel_type": ChannelType.WHATSAPP,
                "display_name": "Live WA",
                "phone_number_id": "live_phone",
                "mock_mode": "",
                "is_active": "on",
            },
        )
        assert response.status_code == 200
        assert b"Live mode requires" in response.content or b"access token" in response.content
