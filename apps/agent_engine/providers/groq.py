"""Groq provider adapter."""
import logging

from django.conf import settings

from apps.agent_engine.providers.base import AICompletionResult, AIProviderAdapter
from apps.agent_engine.providers.mock import MockAIProvider
from apps.agent_engine.services.provider_settings import get_provider_completion_kwargs
from apps.agent_engine.structured_output import STRUCTURED_OUTPUT_JSON_INSTRUCTION

logger = logging.getLogger(__name__)


class GroqProvider(AIProviderAdapter):
    provider_name = "groq"

    def complete(self, system_prompt: str, user_prompt: str, **kwargs) -> AICompletionResult:
        api_key = settings.GROQ_API_KEY
        if not api_key:
            logger.warning("GROQ_API_KEY not set, falling back to mock provider")
            result = MockAIProvider().complete(system_prompt, user_prompt, **kwargs)
            result.metadata = {**(result.metadata or {}), "fallback_used": True, "provider": "mock"}
            return result

        try:
            import httpx

            defaults = get_provider_completion_kwargs("groq")
            model = kwargs.get("model") or defaults["model"]
            temperature = kwargs.get("temperature", defaults["temperature"])
            max_tokens = kwargs.get("max_tokens", defaults["max_tokens"])
            structured_system = system_prompt + "\n\n" + STRUCTURED_OUTPUT_JSON_INSTRUCTION

            response = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": structured_system},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            tokens = usage.get("total_tokens", 0)
            return AICompletionResult(
                text=text,
                confidence=0.85,
                tokens_used=tokens,
                cost_estimate=0.0,
                metadata={"provider": "groq", "model": model, "fallback_used": False},
            )
        except Exception as exc:
            logger.exception("Groq request failed: %s", exc)
            result = MockAIProvider().complete(system_prompt, user_prompt, **kwargs)
            result.metadata = {**(result.metadata or {}), "fallback_used": True, "provider": "mock", "error": str(exc)[:200]}
            return result
