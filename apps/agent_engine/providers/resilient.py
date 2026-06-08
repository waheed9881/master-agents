"""Resilient provider wrapper with fallback support."""
from apps.agent_engine.providers.base import AICompletionResult, AIProviderAdapter
from apps.agent_engine.services.provider_health import complete_with_fallback


class ResilientProviderAdapter(AIProviderAdapter):
    """Wrapper that routes through complete_with_fallback."""

    def __init__(self, provider_name: str | None = None):
        self._requested = provider_name

    @property
    def provider_name(self) -> str:
        from apps.agent_engine.services.provider_health import resolve_provider_name
        return resolve_provider_name(self._requested)

    def complete(self, system_prompt: str, user_prompt: str, **kwargs) -> AICompletionResult:
        return complete_with_fallback(
            system_prompt,
            user_prompt,
            provider_name=self._requested,
            **kwargs,
        )
