"""Knowledge base query helpers."""
from django.db.models import Count, QuerySet

from apps.agents.models import AgentInstance
from apps.knowledge.models import KnowledgeChunk, KnowledgeSource
from apps.tenants.models import Tenant


def list_tenant_knowledge_sources(
    tenant: Tenant,
    agent_instance_id: int | None = None,
) -> QuerySet[KnowledgeSource]:
    qs = (
        KnowledgeSource.objects.filter(tenant=tenant)
        .select_related("agent_instance")
        .annotate(chunk_count=Count("chunks"))
    )
    if agent_instance_id:
        qs = qs.filter(agent_instance_id=agent_instance_id)
    return qs


def get_tenant_knowledge_source(tenant: Tenant, source_id: int) -> KnowledgeSource | None:
    return (
        KnowledgeSource.objects.filter(tenant=tenant, pk=source_id)
        .select_related("agent_instance")
        .prefetch_related("chunks")
        .first()
    )


def get_knowledge_stats(tenant: Tenant, agent_instance: AgentInstance | None = None) -> dict:
    sources = KnowledgeSource.objects.filter(tenant=tenant)
    chunks = KnowledgeChunk.objects.filter(tenant=tenant)
    if agent_instance:
        sources = sources.filter(agent_instance=agent_instance)
        chunks = chunks.filter(source__agent_instance=agent_instance)

    return {
        "total_sources": sources.count(),
        "total_chunks": chunks.count(),
        "by_type": {
            row["source_type"]: row["count"]
            for row in sources.values("source_type").annotate(count=Count("id"))
        },
    }
