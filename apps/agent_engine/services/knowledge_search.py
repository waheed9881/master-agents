"""Knowledge search — agent settings + optional knowledge app (Phase 6)."""
from apps.agents.models import AgentInstance


class KnowledgeSearchService:
    """Search business knowledge for agent context."""

    @classmethod
    def search(cls, agent_instance: AgentInstance, query: str, limit: int = 5) -> list[dict]:
        results: list[dict] = []
        settings = getattr(agent_instance, "settings", None)
        if not settings:
            return results

        query_lower = query.lower()

        if settings.business_description and cls._matches(query_lower, settings.business_description):
            results.append({
                "source": "business_description",
                "text": settings.business_description,
            })

        for i, service in enumerate(settings.services_json or []):
            if cls._matches(query_lower, str(service)):
                results.append({"source": f"service_{i}", "text": str(service)})

        pricing = settings.pricing_json or {}
        if isinstance(pricing, dict):
            for key, value in pricing.items():
                text = f"{key}: {value}"
                if cls._matches(query_lower, text) or cls._matches(query_lower, key):
                    results.append({"source": "pricing", "text": text})

        # Phase 6: search KnowledgeChunk with pgvector or text fallback
        try:
            from apps.knowledge.models import KnowledgeChunk

            chunks = KnowledgeChunk.objects.filter(
                tenant=agent_instance.tenant,
                source__agent_instance=agent_instance,
            )
            for chunk in chunks[:50]:
                if cls._matches(query_lower, chunk.chunk_text):
                    results.append({
                        "source": f"knowledge_chunk_{chunk.pk}",
                        "text": chunk.chunk_text,
                    })
                    if len(results) >= limit:
                        break
        except Exception:
            pass

        return results[:limit]

    @classmethod
    def format_context(cls, results: list[dict]) -> str:
        if not results:
            return ""
        return "\n".join(f"- {r['text']}" for r in results)

    @staticmethod
    def _matches(query: str, text: str) -> bool:
        if not text:
            return False
        text_lower = text.lower()
        if any(word in text_lower for word in query.split() if len(word) > 3):
            return True
        pricing_words = ("price", "cost", "pricing", "plan", "package")
        if any(w in query for w in pricing_words) and any(
            w in text_lower for w in ("price", "cost", "$", "plan", "package")
        ):
            return True
        return False
