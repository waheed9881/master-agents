"""Phase 4 tests: inbox and web chat."""
import pytest
from django.urls import reverse

from apps.accounts.models import User, UserRole
from apps.agents.models import AgentTemplate
from apps.agents.services import create_agent_instance
from apps.inbox.models import Conversation, Message, SenderType
from apps.inbox.services import enable_human_takeover, generate_stub_ai_reply
from apps.tenants.services import create_tenant


@pytest.fixture
def inbox_setup(client, db):
    tenant = create_tenant(name="Inbox Test Co")
    User.objects.create_user(
        email="inboxtest@example.com",
        password="TestPass123!",
        full_name="Inbox Tester",
        tenant=tenant,
        role=UserRole.OWNER,
    )
    template = AgentTemplate.objects.create(
        name="Sales Agent",
        slug="sales-closing-agent",
        description="Test",
        category="Sales",
        is_implemented=True,
    )
    agent = create_agent_instance(tenant, template, status="active")
    client.login(username="inboxtest@example.com", password="TestPass123!")
    return client, tenant, agent


@pytest.mark.django_db
class TestWebChatFlow:
    def test_webchat_message_creates_conversation(self, inbox_setup):
        client, tenant, agent = inbox_setup
        response = client.post(
            "/api/webchat/message/",
            {
                "message_text": "Hello, I need pricing info",
                "customer_name": "Test Customer",
                "customer_email": "customer@test.com",
                "agent_instance_id": agent.pk,
            },
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["conversation_id"]
        assert data["ai_reply"]
        assert Conversation.objects.filter(tenant=tenant).exists()
        assert Message.objects.filter(sender_type=SenderType.CUSTOMER).exists()
        assert Message.objects.filter(sender_type=SenderType.AI).exists()

    def test_webchat_continues_session(self, inbox_setup):
        client, tenant, agent = inbox_setup
        r1 = client.post(
            "/api/webchat/message/",
            {
                "message_text": "Hi there",
                "customer_name": "Session User",
                "agent_instance_id": agent.pk,
            },
            content_type="application/json",
        )
        session_key = r1.json()["session_key"]
        r2 = client.post(
            "/api/webchat/message/",
            {
                "message_text": "Follow up question",
                "session_key": session_key,
                "agent_instance_id": agent.pk,
            },
            content_type="application/json",
        )
        assert r1.json()["conversation_id"] == r2.json()["conversation_id"]
        conv = Conversation.objects.get(pk=r1.json()["conversation_id"])
        assert conv.messages.count() == 4  # 2 customer + 2 ai

    def test_stub_ai_reply_pricing(self, inbox_setup):
        _, _, agent = inbox_setup
        from apps.inbox.services import find_or_create_contact, find_or_create_conversation

        tenant = agent.tenant
        contact = find_or_create_contact(tenant, name="Reply Test")
        conv = find_or_create_conversation(tenant, contact, agent_instance=agent)
        reply = generate_stub_ai_reply("How much does it cost?", conv)
        assert "budget" in reply.lower() or "pricing" in reply.lower()


@pytest.mark.django_db
class TestInboxAPI:
    def test_list_conversations(self, inbox_setup):
        client, tenant, agent = inbox_setup
        client.post(
            "/api/webchat/message/",
            {"message_text": "Test", "agent_instance_id": agent.pk},
            content_type="application/json",
        )
        response = client.get("/api/conversations/")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_human_takeover(self, inbox_setup):
        client, tenant, agent = inbox_setup
        r = client.post(
            "/api/webchat/message/",
            {"message_text": "I want a human", "agent_instance_id": agent.pk},
            content_type="application/json",
        )
        conv_id = r.json()["conversation_id"]
        response = client.post(f"/api/conversations/{conv_id}/human-takeover/")
        assert response.status_code == 200
        conv = Conversation.objects.get(pk=conv_id)
        assert conv.human_takeover is True
        assert conv.ai_enabled is False

    def test_enable_ai_after_takeover(self, inbox_setup):
        client, _, agent = inbox_setup
        r = client.post(
            "/api/webchat/message/",
            {"message_text": "Hello", "agent_instance_id": agent.pk},
            content_type="application/json",
        )
        conv_id = r.json()["conversation_id"]
        enable_human_takeover(Conversation.objects.get(pk=conv_id))
        response = client.post(f"/api/conversations/{conv_id}/enable-ai/")
        assert response.status_code == 200
        conv = Conversation.objects.get(pk=conv_id)
        assert conv.ai_enabled is True
        assert conv.human_takeover is False


@pytest.mark.django_db
class TestInboxViews:
    def test_inbox_list(self, inbox_setup):
        client, _, agent = inbox_setup
        client.post(
            "/api/webchat/message/",
            {"message_text": "Inbox view test", "agent_instance_id": agent.pk},
            content_type="application/json",
        )
        response = client.get(reverse("inbox:list"))
        assert response.status_code == 200
        assert b"Inbox" in response.content

    def test_webchat_demo_page(self, inbox_setup):
        client, _, _ = inbox_setup
        response = client.get(reverse("inbox:webchat_demo"))
        assert response.status_code == 200
        assert b"Web Chat" in response.content


@pytest.mark.django_db
class TestWebhooks:
    def test_whatsapp_webhook_verify(self, client):
        response = client.get(
            "/api/webhooks/whatsapp/",
            {"hub.mode": "subscribe", "hub.verify_token": "ai-agent-os-verify", "hub.challenge": "test123"},
        )
        assert response.status_code == 200
        assert response.content.decode() == "test123"

    def test_instagram_webhook_post_placeholder(self, client):
        response = client.post(
            "/api/webhooks/instagram/",
            {"object": "instagram"},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["status"] == "received"
