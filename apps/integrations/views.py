from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render

from apps.inbox.models import ChannelAccount
from apps.integrations.models import ChannelCredential, WebhookEvent


@login_required
def integrations_index_view(request):
    if not request.tenant:
        raise Http404("No tenant")

    accounts = ChannelAccount.objects.filter(tenant=request.tenant).select_related("credential")
    credentials = ChannelCredential.objects.filter(tenant=request.tenant).select_related("channel_account")
    recent_events = WebhookEvent.objects.filter(tenant=request.tenant).order_by("-received_at")[:10]
    webhook_stats = {
        "total": WebhookEvent.objects.filter(tenant=request.tenant).count(),
        "failed": WebhookEvent.objects.filter(
            tenant=request.tenant, processing_status="failed"
        ).count(),
    }

    return render(
        request,
        "integrations/index.html",
        {
            "page_title": "Integrations",
            "active_nav": "integrations",
            "channel_accounts": accounts,
            "credentials": credentials,
            "recent_events": recent_events,
            "webhook_stats": webhook_stats,
            "mock_mode": getattr(settings, "INTEGRATIONS_MOCK_MODE", True),
            "webhook_urls": {
                "whatsapp": request.build_absolute_uri("/api/webhooks/whatsapp/"),
                "instagram": request.build_absolute_uri("/api/webhooks/instagram/"),
            },
        },
    )
