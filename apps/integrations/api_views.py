from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inbox.models import ChannelAccount
from apps.integrations.models import ChannelCredential, WebhookEvent


def _require_tenant(request):
    if not request.tenant:
        return None, Response({"detail": "No tenant."}, status=status.HTTP_400_BAD_REQUEST)
    return request.tenant, None


class ChannelAccountListAPIView(APIView):
    def get(self, request):
        tenant, err = _require_tenant(request)
        if err:
            return err
        accounts = ChannelAccount.objects.filter(tenant=tenant).select_related("credential")
        data = []
        for account in accounts:
            cred = getattr(account, "credential", None)
            data.append({
                "id": account.pk,
                "channel_type": account.channel_type,
                "display_name": account.display_name,
                "is_active": account.is_active,
                "phone_number_id": cred.phone_number_id if cred else "",
                "page_id": cred.page_id if cred else "",
            })
        return Response(data)


class WebhookEventListAPIView(APIView):
    def get(self, request):
        tenant, err = _require_tenant(request)
        if err:
            return err
        events = WebhookEvent.objects.filter(tenant=tenant).order_by("-received_at")[:50]
        return Response([
            {
                "id": e.pk,
                "channel_type": e.channel_type,
                "external_message_id": e.external_message_id,
                "processing_status": e.processing_status,
                "event_type": e.event_type,
                "error_message": e.error_message,
                "received_at": e.received_at.isoformat(),
            }
            for e in events
        ])
