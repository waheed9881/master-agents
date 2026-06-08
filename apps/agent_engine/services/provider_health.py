"""Provider availability checks and safe fallback selection."""
from __future__ import annotations

import logging

from apps.agent_engine.providers.base import AICompletionResult
from apps.agent_engine.services.provider_settings import (
    get_configured_provider,
    get_fallback_provider,
    get_provider_completion_kwargs,
    get_provider_status,
)

logger = logging.getLogger(__name__)


def is_provider_available(provider: str) -> bool:
    status = get_provider_status(provider)
    return bool(status["available"])


def resolve_provider_name(requested: str | None = None) -> str:
    """Return provider to use; fall back when key missing."""
    name = (requested or get_configured_provider()).lower()
    if name == "mock":
        return "mock"
    if is_provider_available(name):
        return name
    fallback = get_fallback_provider()
    logger.warning("Provider %s unavailable, using fallback %s", name, fallback)
    return fallback


def complete_with_fallback(
    system_prompt: str,
    user_prompt: str,
    *,
    provider_name: str | None = None,
    **kwargs,
) -> AICompletionResult:
    """Call provider with settings kwargs; annotate fallback in metadata."""
    from apps.agent_engine.providers.factory import get_ai_provider

    requested = (provider_name or get_configured_provider()).lower()
    resolved = resolve_provider_name(requested)
    completion_kwargs = {**get_provider_completion_kwargs(resolved), **kwargs}

    primary = get_ai_provider(resolved, resilient=False)
    result = primary.complete(system_prompt, user_prompt, **completion_kwargs)

    meta = dict(result.metadata or {})
    meta.setdefault("provider_requested", requested)
    meta["provider_resolved"] = resolved
    meta["model"] = completion_kwargs.get("model", "")

    fallback_used = requested != resolved or meta.get("fallback_used", False)
    if resolved == "mock" and requested != "mock":
        fallback_used = True
    meta["fallback_used"] = fallback_used
    result.metadata = meta
    return result
