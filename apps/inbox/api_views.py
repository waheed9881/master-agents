from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inbox import selectors, services
from apps.inbox.models import SenderType
from apps.inbox.serializers import (
    ConversationDetailSerializer,
    ConversationListSerializer,
    SendMessageSerializer,
)
from apps.integrations.webchat import handle_webchat_message


def _require_tenant(request):
    if not request.tenant:
        return None, Response({"detail": "No tenant."}, status=status.HTTP_400_BAD_REQUEST)
    return request.tenant, None


class ConversationListAPIView(APIView):
    def get(self, request):
        tenant, err = _require_tenant(request)
        if err:
            return err
        conversations = selectors.list_tenant_conversations(tenant)
        channel = request.query_params.get("channel")
        if channel:
            conversations = conversations.filter(channel_type=channel)
        return Response(ConversationListSerializer(conversations, many=True).data)


class ConversationDetailAPIView(APIView):
    def get(self, request, conversation_id):
        tenant, err = _require_tenant(request)
        if err:
            return err
        conversation = selectors.get_tenant_conversation(tenant, conversation_id)
        if not conversation:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ConversationDetailSerializer(conversation).data)


class ConversationSendMessageAPIView(APIView):
    def post(self, request, conversation_id):
        tenant, err = _require_tenant(request)
        if err:
            return err
        conversation = selectors.get_tenant_conversation(tenant, conversation_id)
        if not conversation:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        text = serializer.validated_data["message_text"]

        if conversation.human_takeover or not conversation.ai_enabled:
            msg = services.send_human_reply(conversation, text, request.user)
        else:
            msg = services.create_message(
                conversation,
                sender_type=SenderType.HUMAN,
                message_text=text,
                metadata={"user_id": request.user.pk, "staff_reply": True},
            )

        return Response(
            {"message_id": msg.pk, "sender_type": msg.sender_type},
            status=status.HTTP_201_CREATED,
        )


class HumanTakeoverAPIView(APIView):
    def post(self, request, conversation_id):
        tenant, err = _require_tenant(request)
        if err:
            return err
        conversation = selectors.get_tenant_conversation(tenant, conversation_id)
        if not conversation:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        services.enable_human_takeover(conversation)
        return Response({"human_takeover": True, "ai_enabled": False})


class EnableAIAPIView(APIView):
    def post(self, request, conversation_id):
        tenant, err = _require_tenant(request)
        if err:
            return err
        conversation = selectors.get_tenant_conversation(tenant, conversation_id)
        if not conversation:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        services.enable_ai(conversation)
        return Response({"human_takeover": False, "ai_enabled": True})


class WebChatMessageAPIView(APIView):
    """Public-facing web chat endpoint (authenticated demo)."""

    def post(self, request):
        tenant, err = _require_tenant(request)
        if err:
            return err

        from apps.inbox.serializers import WebChatMessageSerializer

        serializer = WebChatMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = handle_webchat_message(
            tenant,
            message_text=data["message_text"],
            customer_name=data.get("customer_name", "Web Chat Visitor"),
            customer_email=data.get("customer_email", ""),
            customer_phone=data.get("customer_phone", ""),
            agent_instance_id=data.get("agent_instance_id"),
            session_key=data.get("session_key", ""),
        )
        return Response(result, status=status.HTTP_201_CREATED)
