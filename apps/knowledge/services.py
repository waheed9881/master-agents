"""Knowledge base business logic."""
import re

from django.db.models import Q

from apps.agents.models import AgentInstance
from apps.knowledge.models import KnowledgeChunk, KnowledgeSource, KnowledgeSourceType
from apps.tenants.models import Tenant

CHUNK_MAX_CHARS = 500


def chunk_text(text: str, max_chars: int = CHUNK_MAX_CHARS) -> list[str]:
    """Split text into paragraph-aware chunks for search."""
    text = text.strip()
    if not text:
        return []

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            sentences = re.split(r"(?<=[.!?])\s+", paragraph)
            for sentence in sentences:
                while len(sentence) > max_chars:
                    chunks.append(sentence[:max_chars].strip())
                    sentence = sentence[max_chars:].strip()
                if len(current) + len(sentence) + 1 <= max_chars:
                    current = f"{current} {sentence}".strip()
                else:
                    if current:
                        chunks.append(current.strip())
                    current = sentence
            continue

        if len(current) + len(paragraph) + 2 <= max_chars:
            current = f"{current}\n\n{paragraph}".strip() if current else paragraph
        else:
            if current:
                chunks.append(current.strip())
            current = paragraph

    if current:
        chunks.append(current.strip())

    return chunks or [text[:max_chars]]


def create_chunks_for_source(source: KnowledgeSource) -> list[KnowledgeChunk]:
    """Create or refresh chunks for a knowledge source."""
    source.chunks.all().delete()
    chunks = []
    for index, text in enumerate(chunk_text(source.content)):
        chunk = KnowledgeChunk.objects.create(
            tenant=source.tenant,
            source=source,
            chunk_text=text,
            metadata_json={"index": index, "source_type": source.source_type},
        )
        chunks.append(chunk)
    return chunks


def create_knowledge_source(
    tenant: Tenant,
    *,
    title: str,
    content: str,
    source_type: str = KnowledgeSourceType.TEXT,
    agent_instance: AgentInstance | None = None,
) -> KnowledgeSource:
    """Create a knowledge source and its searchable chunks."""
    source = KnowledgeSource.objects.create(
        tenant=tenant,
        agent_instance=agent_instance,
        title=title,
        content=content,
        source_type=source_type,
    )
    create_chunks_for_source(source)
    return source


def update_knowledge_source(source: KnowledgeSource, **fields) -> KnowledgeSource:
    """Update source fields and re-chunk when content changes."""
    content_changed = "content" in fields and fields["content"] != source.content
    for key, value in fields.items():
        setattr(source, key, value)
    source.save()
    if content_changed:
        create_chunks_for_source(source)
    return source


def search_knowledge_for_agent(
    agent_instance: AgentInstance,
    query: str,
    limit: int = 5,
) -> list[dict]:
    """Text-search knowledge chunks scoped to an agent instance."""
    query = query.strip()
    if not query:
        return []

    chunks = KnowledgeChunk.objects.filter(
        tenant=agent_instance.tenant,
        source__agent_instance=agent_instance,
    ).select_related("source")

    words = [w.lower() for w in query.split() if len(w) > 2]
    if not words:
        words = [query.lower()]

    q_filter = Q()
    for word in words:
        q_filter |= Q(chunk_text__icontains=word)

    pricing_words = ("price", "cost", "pricing", "plan", "package", "fee")
    if any(w in query.lower() for w in pricing_words):
        q_filter |= Q(source__source_type=KnowledgeSourceType.PRICING)

    matched = chunks.filter(q_filter).distinct()[:limit]

    return [
        {
            "source": f"knowledge_chunk_{chunk.pk}",
            "text": chunk.chunk_text,
            "title": chunk.source.title,
            "source_type": chunk.source.source_type,
        }
        for chunk in matched
    ]
