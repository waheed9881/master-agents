"""Template context for tenant and navigation."""


def tenant_context(request):
    tenant = getattr(request, "tenant", None)
    return {
        "current_tenant": tenant,
    }
