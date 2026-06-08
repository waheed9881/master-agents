"""WhatsApp webhook — Meta Cloud API verification and inbound messages."""
import json
import logging

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.integrations.services.webhook_processor import WebhookProcessorService

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def whatsapp_webhook(request):
    if request.method == "GET":
        challenge = WebhookProcessorService.verify_subscription(
            request.GET.get("hub.verify_token", ""),
            request.GET.get("hub.challenge", ""),
            request.GET.get("hub.mode", ""),
        )
        if challenge is not None:
            return HttpResponse(challenge, content_type="text/plain")
        return HttpResponse("Forbidden", status=403)

    from apps.accounts.rate_limit import get_rate_limit_for_scope, rate_limit_or_429

    limit, window = get_rate_limit_for_scope("webhook")
    blocked = rate_limit_or_429(request, "webhook", limit, window)
    if blocked:
        return blocked

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    signature = request.headers.get("X-Hub-Signature-256", "")
    result = WebhookProcessorService.process(
        "whatsapp",
        payload,
        raw_body=request.body,
        signature=signature,
    )
    if result.get("status") == "forbidden":
        return JsonResponse(result, status=403)
    return JsonResponse(result)
