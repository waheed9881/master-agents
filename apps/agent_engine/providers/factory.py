"""Factory for AI provider adapters."""
from django.conf import settings

from apps.agent_engine.providers.base import AIProviderAdapter
from apps.agent_engine.providers.gemini import GeminiProvider
from apps.agent_engine.providers.groq import GroqProvider
from apps.agent_engine.providers.mock import MockAIProvider
from apps.agent_engine.providers.openai import OpenAIProvider

_PROVIDERS: dict[str, type[AIProviderAdapter]] = {
    "mock": MockAIProvider,
    "openai": OpenAIProvider,
    "groq": GroqProvider,
    "gemini": GeminiProvider,
}


def get_ai_provider(name: str | None = None) -> AIProviderAdapter:
    """Return configured AI provider, defaulting to mock when keys missing."""
    provider_name = (name or settings.AI_PROVIDER or "mock").lower()
    cls = _PROVIDERS.get(provider_name, MockAIProvider)
    return cls()
