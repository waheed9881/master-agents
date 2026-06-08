"""Knowledge search — agent settings + knowledge base chunks."""
from apps.agents.models import AgentInstance


class KnowledgeSearchService:
    """Search business knowledge for agent context."""

    @classmethod
    def search(cls, agent_instance: AgentInstance, query: str, limit: int = 5) -> list[dict]:
        results: list[dict] = []
        settings = getattr(agent_instance, "settings", None)
        if not settings:
            settings_results = []
        else:
            settings_results = cls._search_agent_settings(settings, query, limit)
        results.extend(settings_results)

        remaining = limit - len(results)
        if remaining > 0:
            chunk_results = cls._search_knowledge_chunks(agent_instance, query, remaining)
            results.extend(chunk_results)

        return results[:limit]

    @classmethod
    def _search_agent_settings(cls, settings, query: str, limit: int) -> list[dict]:
        results: list[dict] = []
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

        return results[:limit]

    @classmethod
    def _search_knowledge_chunks(
        cls,
        agent_instance: AgentInstance,
        query: str,
        limit: int,
    ) -> list[dict]:
        try:
            from apps.knowledge.services import search_knowledge_for_agent

            return search_knowledge_for_agent(agent_instance, query, limit=limit)
        except Exception:
            return []

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
