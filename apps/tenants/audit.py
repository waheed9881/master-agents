"""Security and workspace audit logging."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from django.http import HttpRequest

    from apps.accounts.models import User
    from apps.tenants.models import Tenant


def log_audit_event(
    *,
    action: str,
    tenant: "Tenant | None" = None,
    user: "User | None" = None,
    object_type: str = "",
    object_id: str = "",
    metadata: dict[str, Any] | None = None,
    request: "HttpRequest | None" = None,
) -> None:
    """Create an audit log entry. Fails silently if model unavailable."""
    try:
        from apps.accounts.rate_limit import get_client_ip
        from apps.tenants.models import AuditLog

        ip = get_client_ip(request) if request else None
        AuditLog.objects.create(
            tenant=tenant,
            user=user,
            action=action,
            object_type=object_type,
            object_id=str(object_id) if object_id else "",
            metadata=metadata or {},
            ip_address=ip,
        )
    except Exception:
        pass
