"""Google Gemini provider adapter."""
import logging

from django.conf import settings

from apps.agent_engine.providers.base import AICompletionResult, AIProviderAdapter
from apps.agent_engine.providers.mock import MockAIProvider

logger = logging.getLogger(__name__)


class GeminiProvider(AIProviderAdapter):
    provider_name = "gemini"

    def complete(self, system_prompt: str, user_prompt: str, **kwargs) -> AICompletionResult:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            logger.warning("GEMINI_API_KEY not set, falling back to mock provider")
            return MockAIProvider().complete(system_prompt, user_prompt, **kwargs)

        try:
            import httpx

            model = kwargs.get("model", "gemini-1.5-flash")
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
                f"?key={api_key}"
            )
            response = httpx.post(
                url,
                json={
                    "contents": [{"parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}],
                    "generationConfig": {"temperature": kwargs.get("temperature", 0.7)},
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            tokens = len(text.split()) * 2
            return AICompletionResult(
                text=text,
                confidence=0.85,
                tokens_used=tokens,
                cost_estimate=0.0,
                metadata={"provider": "gemini", "model": model},
            )
        except Exception as exc:
            logger.exception("Gemini request failed: %s", exc)
            return MockAIProvider().complete(system_prompt, user_prompt, **kwargs)
