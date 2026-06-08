"""
Instagram webhook placeholder.

TODO: Implement Meta Instagram Messaging API.
- GET: Webhook verification (hub.verify_token, hub.challenge)
- POST: Parse Instagram DM events and route to InboundMessageService
"""
import json
import logging

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

INSTAGRAM_VERIFY_TOKEN = getattr(settings, "INSTAGRAM_VERIFY_TOKEN", "ai-agent-os-verify")


@csrf_exempt
@require_http_methods(["GET", "POST"])
def instagram_webhook(request):
    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")
        if mode == "subscribe" and token == INSTAGRAM_VERIFY_TOKEN:
            return HttpResponse(challenge, content_type="text/plain")
        return HttpResponse("Forbidden", status=403)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    logger.info("Instagram webhook received (placeholder): %s", payload.get("object"))

    # TODO: Extract sender_id, message text, tenant mapping
    # TODO: Call InboundMessageService.process(channel_type=ChannelType.INSTAGRAM)

    return JsonResponse({"status": "received", "note": "Instagram processing not yet implemented"})
