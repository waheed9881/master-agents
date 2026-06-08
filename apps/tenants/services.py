"""Tenant creation and lookup services."""
from apps.tenants.models import Tenant


def create_tenant(
    name: str,
    *,
    country: str = "",
    industry: str = "",
    timezone: str = "UTC",
    default_currency: str = "USD",
) -> Tenant:
    """Create a new tenant workspace."""
    return Tenant.objects.create(
        name=name,
        country=country,
        industry=industry,
        timezone=timezone,
        default_currency=default_currency,
    )


def get_tenant_by_slug(slug: str) -> Tenant | None:
    return Tenant.objects.filter(slug=slug).first()
