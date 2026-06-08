from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.agent_engine.serializers import TestMessageSerializer
from apps.agents.models import AgentInstance
from apps.integrations.webchat import handle_webchat_message


class TestMessageAPIView(APIView):
    """Test agent engine with a message without persisting full webchat flow."""

    def post(self, request):
        if not request.tenant:
            return Response({"detail": "No tenant."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = TestMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        agent = AgentInstance.objects.filter(
            tenant=request.tenant,
            pk=data["agent_instance_id"],
        ).first()
        if not agent:
            return Response({"detail": "Agent not found."}, status=status.HTTP_404_NOT_FOUND)

        result = handle_webchat_message(
            request.tenant,
            message_text=data["message_text"],
            customer_name=data.get("customer_name", "Test Customer"),
            customer_email=data.get("customer_email", ""),
            agent_instance_id=agent.pk,
            session_key=data.get("session_key", ""),
        )
        return Response(result, status=status.HTTP_201_CREATED)
