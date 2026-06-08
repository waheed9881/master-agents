"""Google Gemini provider adapter."""
import logging

from django.conf import settings

from apps.agent_engine.providers.base import AICompletionResult, AIProviderAdapter
from apps.agent_engine.providers.mock import MockAIProvider
from apps.agent_engine.services.provider_settings import get_provider_completion_kwargs
from apps.agent_engine.structured_output import STRUCTURED_OUTPUT_JSON_INSTRUCTION

logger = logging.getLogger(__name__)


class GeminiProvider(AIProviderAdapter):
    provider_name = "gemini"

    def complete(self, system_prompt: str, user_prompt: str, **kwargs) -> AICompletionResult:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            logger.warning("GEMINI_API_KEY not set, falling back to mock provider")
            result = MockAIProvider().complete(system_prompt, user_prompt, **kwargs)
            result.metadata = {**(result.metadata or {}), "fallback_used": True, "provider": "mock"}
            return result

        try:
            import httpx

            defaults = get_provider_completion_kwargs("gemini")
            model = kwargs.get("model") or defaults["model"]
            temperature = kwargs.get("temperature", defaults["temperature"])
            structured_system = system_prompt + "\n\n" + STRUCTURED_OUTPUT_JSON_INSTRUCTION
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
                f"?key={api_key}"
            )
            response = httpx.post(
                url,
                json={
                    "contents": [{"parts": [{"text": f"{structured_system}\n\n{user_prompt}"}]}],
                    "generationConfig": {"temperature": temperature, "maxOutputTokens": kwargs.get("max_tokens", defaults["max_tokens"])},
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
                metadata={"provider": "gemini", "model": model, "fallback_used": False},
            )
        except Exception as exc:
            logger.exception("Gemini request failed: %s", exc)
            result = MockAIProvider().complete(system_prompt, user_prompt, **kwargs)
            result.metadata = {**(result.metadata or {}), "fallback_used": True, "provider": "mock", "error": str(exc)[:200]}
            return result
