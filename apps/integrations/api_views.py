from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.agents import selectors as agent_selectors
from apps.inbox.models import ChannelAccount
from apps.integrations.forms import ChannelAccountForm
from apps.integrations.models import WebhookEvent
from apps.integrations.services.channel_credentials import mask_credential_value
from apps.integrations.services.channel_service import (
    account_form_initial,
    create_channel_account,
    simulate_test_message,
    update_channel_account,
)


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
                "mock_mode": account.mock_mode,
                "phone_number_id": cred.phone_number_id if cred else "",
                "page_id": cred.page_id if cred else "",
                "business_account_id": cred.business_account_id if cred else "",
                "access_token_masked": mask_credential_value(cred.access_token_encrypted) if cred else "",
                "app_secret_masked": mask_credential_value(cred.app_secret_encrypted) if cred else "",
            })
        return Response(data)

    def post(self, request):
        tenant, err = _require_tenant(request)
        if err:
            return err
        form = ChannelAccountForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
        account = create_channel_account(
            tenant, form, user=request.user, request=request
        )
        return Response({"id": account.pk, "display_name": account.display_name}, status=status.HTTP_201_CREATED)


class ChannelAccountDetailAPIView(APIView):
    def get(self, request, account_id):
        tenant, err = _require_tenant(request)
        if err:
            return err
        account = ChannelAccount.objects.filter(pk=account_id, tenant=tenant).select_related("credential").first()
        if not account:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        cred = getattr(account, "credential", None)
        return Response({
            "id": account.pk,
            "channel_type": account.channel_type,
            "display_name": account.display_name,
            "is_active": account.is_active,
            "mock_mode": account.mock_mode,
            "phone_number_id": cred.phone_number_id if cred else "",
            "page_id": cred.page_id if cred else "",
            "business_account_id": cred.business_account_id if cred else "",
            "verify_token": cred.verify_token if cred else "",
            "access_token_masked": mask_credential_value(cred.access_token_encrypted) if cred else "",
            "app_secret_masked": mask_credential_value(cred.app_secret_encrypted) if cred else "",
        })

    def patch(self, request, account_id):
        tenant, err = _require_tenant(request)
        if err:
            return err
        account = ChannelAccount.objects.filter(pk=account_id, tenant=tenant).first()
        if not account:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        merged = account_form_initial(account)
        merged.update(request.data)
        form = ChannelAccountForm(merged)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
        update_channel_account(
            account, form, user=request.user, request=request
        )
        return Response({"id": account.pk, "display_name": account.display_name})


class ChannelTestMessageAPIView(APIView):
    def post(self, request, account_id):
        tenant, err = _require_tenant(request)
        if err:
            return err
        account = ChannelAccount.objects.filter(pk=account_id, tenant=tenant).first()
        if not account:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        agent_id = request.data.get("agent_instance_id")
        agent = agent_selectors.get_tenant_agent(tenant, agent_id) if agent_id else None
        if not agent:
            return Response({"detail": "Agent not found."}, status=status.HTTP_400_BAD_REQUEST)

        result = simulate_test_message(
            tenant,
            account,
            message_text=request.data.get("message_text", "Hello"),
            customer_name=request.data.get("customer_name", "API Test"),
            customer_phone=request.data.get("customer_phone", ""),
            customer_username=request.data.get("customer_username", ""),
            agent_instance=agent,
        )
        return Response(result)


class WebhookEventListAPIView(APIView):
    def get(self, request):
        tenant, err = _require_tenant(request)
        if err:
            return err
        events = WebhookEvent.objects.filter(tenant=tenant).select_related("conversation").order_by("-received_at")[:50]
        return Response([
            {
                "id": e.pk,
                "channel_type": e.channel_type,
                "external_message_id": e.external_message_id,
                "processing_status": e.processing_status,
                "event_type": e.event_type,
                "error_message": e.error_message,
                "received_at": e.received_at.isoformat(),
                "conversation_id": e.conversation_id,
            }
            for e in events
        ])
