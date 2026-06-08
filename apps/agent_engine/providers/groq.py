"""Groq provider adapter."""
import logging

from django.conf import settings

from apps.agent_engine.providers.base import AICompletionResult, AIProviderAdapter
from apps.agent_engine.providers.mock import MockAIProvider

logger = logging.getLogger(__name__)


class GroqProvider(AIProviderAdapter):
    provider_name = "groq"

    def complete(self, system_prompt: str, user_prompt: str, **kwargs) -> AICompletionResult:
        api_key = settings.GROQ_API_KEY
        if not api_key:
            logger.warning("GROQ_API_KEY not set, falling back to mock provider")
            return MockAIProvider().complete(system_prompt, user_prompt, **kwargs)

        try:
            import httpx

            model = kwargs.get("model", "llama-3.1-8b-instant")
            response = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_tokens": kwargs.get("max_tokens", 512),
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
                metadata={"provider": "groq", "model": model},
            )
        except Exception as exc:
            logger.exception("Groq request failed: %s", exc)
            return MockAIProvider().complete(system_prompt, user_prompt, **kwargs)
