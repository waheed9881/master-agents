"""Lightweight rate limiting using Django cache with in-memory fallback."""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse

if TYPE_CHECKING:
    from django.http import HttpRequest

_memory_buckets: dict[str, list[float]] = {}


def get_client_ip(request: "HttpRequest") -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _rate_limiting_enabled() -> bool:
    return getattr(settings, "RATE_LIMITING_ENABLED", True)


def _memory_check(key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
    now = time.time()
    cutoff = now - window_seconds
    bucket = _memory_buckets.setdefault(key, [])
    bucket[:] = [t for t in bucket if t > cutoff]
    if len(bucket) >= limit:
        return False, 0
    bucket.append(now)
    remaining = max(0, limit - len(bucket))
    return True, remaining


def check_rate_limit(key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
    """
    Return (allowed, remaining).
    allowed=False when limit exceeded.
    """
    if not _rate_limiting_enabled():
        return True, limit

    cache_key = f"ratelimit:{key}"
    try:
        current = cache.get(cache_key)
        if current is None:
            cache.set(cache_key, 1, timeout=window_seconds)
            return True, limit - 1
        if current >= limit:
            return False, 0
        try:
            new_count = cache.incr(cache_key)
        except ValueError:
            cache.set(cache_key, 1, timeout=window_seconds)
            return True, limit - 1
        return True, max(0, limit - new_count)
    except Exception:
        return _memory_check(cache_key, limit, window_seconds)


def rate_limit_or_429(
    request: "HttpRequest",
    scope: str,
    limit: int,
    window_seconds: int = 60,
    *,
    tenant=None,
    user=None,
    json_response: bool = True,
) -> HttpResponse | JsonResponse | None:
    """
    Check rate limit for request. Returns 429 response if exceeded, else None.
    Logs audit entry when limit is hit.
    """
    if not _rate_limiting_enabled():
        return None

    ip = get_client_ip(request)
    key = f"{scope}:{ip}"
    if user and getattr(user, "is_authenticated", False):
        key = f"{scope}:user:{user.pk}"
    elif tenant:
        key = f"{scope}:tenant:{tenant.pk}:{ip}"

    allowed, remaining = check_rate_limit(key, limit, window_seconds)
    if allowed:
        return None

    from apps.tenants.audit import log_audit_event

    log_audit_event(
        action="rate_limit_exceeded",
        tenant=tenant,
        user=user if getattr(user, "is_authenticated", False) else None,
        object_type="rate_limit",
        object_id=scope,
        metadata={"scope": scope, "limit": limit, "ip": ip},
        request=request,
    )

    message = (
        f"Rate limit exceeded for {scope.replace('_', ' ')}. "
        f"Please wait {window_seconds} seconds and try again."
    )
    if json_response:
        return JsonResponse(
            {"detail": message, "scope": scope, "retry_after_seconds": window_seconds},
            status=429,
        )
    return HttpResponse(message, status=429, content_type="text/plain")


def get_rate_limit_for_scope(scope: str) -> tuple[int, int]:
    """Return (limit, window_seconds) for a named scope."""
    mapping = {
        "webchat": (
            getattr(settings, "RATE_LIMIT_WEBCHAT_PER_MINUTE", 30),
            60,
        ),
        "webhook": (
            getattr(settings, "RATE_LIMIT_WEBHOOK_PER_MINUTE", 120),
            60,
        ),
        "provider_test": (
            getattr(settings, "RATE_LIMIT_PROVIDER_TEST_PER_MINUTE", 20),
            60,
        ),
        "login": (
            getattr(settings, "RATE_LIMIT_LOGIN_PER_MINUTE", 10),
            60,
        ),
        "playground": (
            getattr(settings, "RATE_LIMIT_PLAYGROUND_PER_MINUTE", 30),
            60,
        ),
    }
    return mapping.get(scope, (60, 60))
