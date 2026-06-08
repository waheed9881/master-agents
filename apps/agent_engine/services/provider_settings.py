"""Read AI provider configuration from environment (no secrets exposed)."""
from __future__ import annotations

from django.conf import settings

PROVIDER_KEY_ENV = {
    "openai": "OPENAI_API_KEY",
    "groq": "GROQ_API_KEY",
    "gemini": "GEMINI_API_KEY",
}

DEFAULT_MODELS = {
    "mock": "mock-local",
    "openai": "gpt-4o-mini",
    "groq": "llama-3.1-8b-instant",
    "gemini": "gemini-1.5-flash",
}


def _has_key(provider: str) -> bool:
    env_name = PROVIDER_KEY_ENV.get(provider)
    if not env_name:
        return True
    return bool(getattr(settings, env_name, ""))


def get_configured_provider() -> str:
    return (getattr(settings, "AI_PROVIDER", "mock") or "mock").lower()


def get_fallback_provider() -> str:
    return (getattr(settings, "AI_FALLBACK_PROVIDER", "mock") or "mock").lower()


def get_model_name(provider: str | None = None) -> str:
    provider = (provider or get_configured_provider()).lower()
    configured = getattr(settings, "AI_MODEL_NAME", "") or ""
    if configured:
        return configured
    return DEFAULT_MODELS.get(provider, "mock-local")


def get_max_tokens() -> int:
    return int(getattr(settings, "AI_MAX_TOKENS", 800) or 800)


def get_temperature() -> float:
    return float(getattr(settings, "AI_TEMPERATURE", 0.3) or 0.3)


def get_daily_token_budget() -> int | None:
    value = getattr(settings, "AI_DAILY_TOKEN_BUDGET", "") or ""
    return int(value) if str(value).isdigit() else None


def get_monthly_token_budget() -> int | None:
    value = getattr(settings, "AI_MONTHLY_TOKEN_BUDGET", "") or ""
    return int(value) if str(value).isdigit() else None


def get_provider_completion_kwargs(provider: str | None = None) -> dict:
    return {
        "model": get_model_name(provider),
        "temperature": get_temperature(),
        "max_tokens": get_max_tokens(),
    }


def get_provider_status(provider: str | None = None) -> dict:
    """Safe provider status for UI/API — never includes raw API keys."""
    provider = (provider or get_configured_provider()).lower()
    fallback = get_fallback_provider()
    api_key_configured = _has_key(provider) if provider != "mock" else True

    return {
        "provider": provider,
        "model": get_model_name(provider),
        "api_key_configured": api_key_configured,
        "available": provider == "mock" or api_key_configured,
        "fallback_provider": fallback,
        "max_tokens": get_max_tokens(),
        "temperature": get_temperature(),
        "daily_token_budget": get_daily_token_budget(),
        "monthly_token_budget": get_monthly_token_budget(),
        "mock_mode": provider == "mock",
        "keys_status": {
            name: _has_key(name) for name in ("openai", "groq", "gemini")
        },
    }


def get_all_providers_status() -> list[dict]:
    providers = ["mock", "openai", "groq", "gemini"]
    current = get_configured_provider()
    rows = []
    for name in providers:
        row = get_provider_status(name)
        row["is_active"] = name == current
        rows.append(row)
    return rows
