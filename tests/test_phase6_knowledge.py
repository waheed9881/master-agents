"""Phase 6 tests: knowledge base module."""
import io

import pytest

from apps.accounts.models import User, UserRole
from apps.agent_engine.services.knowledge_search import KnowledgeSearchService
from apps.agents.models import AgentTemplate
from apps.agents.services import create_agent_instance, update_agent_settings
from apps.knowledge.models import KnowledgeChunk, KnowledgeSource, KnowledgeSourceType
from apps.knowledge.services import (
    chunk_text,
    create_knowledge_source,
    search_knowledge_for_agent,
)
from apps.tenants.services import create_tenant


@pytest.fixture
def knowledge_client(client, db):
    tenant = create_tenant(name="Knowledge Test Co")
    User.objects.create_user(
        email="kbtest@example.com",
        password="TestPass123!",
        full_name="KB Tester",
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
    update_agent_settings(
        agent,
        business_name="KB Corp",
        pricing_json={"Starter": "$299/month"},
    )
    client.login(username="kbtest@example.com", password="TestPass123!")
    return client, tenant, agent


@pytest.mark.django_db
class TestChunking:
    def test_chunk_text_splits_long_content(self):
        content = "Paragraph one.\n\n" + ("Word " * 120)
        chunks = chunk_text(content, max_chars=200)
        assert len(chunks) >= 2
        assert all(len(c) <= 250 for c in chunks)

    def test_create_source_generates_chunks(self, knowledge_client):
        _, tenant, agent = knowledge_client
        source = create_knowledge_source(
            tenant,
            title="Test FAQ",
            content="Question one?\n\nAnswer one.\n\nQuestion two?\n\nAnswer two.",
            source_type=KnowledgeSourceType.FAQ,
            agent_instance=agent,
        )
        assert source.pk
        assert KnowledgeChunk.objects.filter(source=source).count() >= 1


@pytest.mark.django_db
class TestKnowledgeSearch:
    def test_search_finds_pricing_chunk(self, knowledge_client):
        _, tenant, agent = knowledge_client
        create_knowledge_source(
            tenant,
            title="Pricing",
            content="Growth plan costs $599 per month with WhatsApp support.",
            source_type=KnowledgeSourceType.PRICING,
            agent_instance=agent,
        )
        results = search_knowledge_for_agent(agent, "What is your pricing?")
        assert results
        assert any("599" in r["text"] for r in results)

    def test_agent_engine_search_includes_knowledge(self, knowledge_client):
        _, tenant, agent = knowledge_client
        create_knowledge_source(
            tenant,
            title="Refund Policy",
            content="Refunds are prorated within the billing period.",
            source_type=KnowledgeSourceType.POLICY,
            agent_instance=agent,
        )
        results = KnowledgeSearchService.search(agent, "refund policy")
        assert any("prorated" in r["text"].lower() for r in results)


@pytest.mark.django_db
class TestKnowledgeAPI:
    def test_list_knowledge_sources(self, knowledge_client):
        client, tenant, agent = knowledge_client
        create_knowledge_source(
            tenant,
            title="API Source",
            content="Sample knowledge content for API test.",
            agent_instance=agent,
        )
        response = client.get("/api/knowledge/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["title"] == "API Source"

    def test_create_knowledge_source(self, knowledge_client):
        client, _, agent = knowledge_client
        response = client.post(
            "/api/knowledge/",
            {
                "title": "New FAQ",
                "content": "We offer 24/7 support on Enterprise plans.",
                "source_type": "faq",
                "agent_instance_id": agent.pk,
            },
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["chunk_count"] >= 1
        assert KnowledgeSource.objects.filter(title="New FAQ").exists()

    def test_upload_knowledge_file(self, knowledge_client):
        client, _, agent = knowledge_client
        file_content = io.BytesIO(b"Uploaded policy text for testing.")
        response = client.post(
            "/api/knowledge/upload/",
            {
                "file": file_content,
                "title": "Uploaded Doc",
                "agent_instance_id": agent.pk,
            },
        )
        assert response.status_code == 201
        assert KnowledgeSource.objects.filter(title="Uploaded Doc").exists()


@pytest.mark.django_db
class TestKnowledgeUI:
    def test_knowledge_list_page(self, knowledge_client):
        client, tenant, agent = knowledge_client
        create_knowledge_source(
            tenant,
            title="UI Source",
            content="Visible on knowledge page.",
            agent_instance=agent,
        )
        response = client.get("/knowledge/")
        assert response.status_code == 200
        assert b"UI Source" in response.content

    def test_knowledge_source_detail_page(self, knowledge_client):
        client, tenant, agent = knowledge_client
        source = create_knowledge_source(
            tenant,
            title="Detail Source",
            content="Detail page content.",
            agent_instance=agent,
        )
        response = client.get(f"/knowledge/sources/{source.pk}/")
        assert response.status_code == 200
        assert b"Detail page content." in response.content
