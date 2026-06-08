"""
WhatsApp webhook placeholder.

TODO: Implement Meta Cloud API verification and message handling.
- GET: hub.verify_token, hub.challenge for webhook verification
- POST: Parse incoming WhatsApp messages and route to InboundMessageService
"""
import hashlib
import hmac
import json
import logging

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

WHATSAPP_VERIFY_TOKEN = getattr(settings, "WHATSAPP_VERIFY_TOKEN", "ai-agent-os-verify")


@csrf_exempt
@require_http_methods(["GET", "POST"])
def whatsapp_webhook(request):
    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")
        if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
            return HttpResponse(challenge, content_type="text/plain")
        return HttpResponse("Forbidden", status=403)

    # POST — incoming message (placeholder)
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    logger.info("WhatsApp webhook received (placeholder): %s", payload.get("object"))

    # TODO: Extract tenant from phone_number_id mapping
    # TODO: Normalize message and call InboundMessageService.process()

    return JsonResponse({"status": "received", "note": "WhatsApp processing not yet implemented"})


def verify_whatsapp_signature(payload: bytes, signature: str, app_secret: str) -> bool:
    """Verify X-Hub-Signature-256 header from Meta."""
    if not signature or not app_secret:
        return False
    expected = "sha256=" + hmac.new(
        app_secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
