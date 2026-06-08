from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.agents import selectors, services
from apps.agents.models import AgentSettings
from apps.agents.serializers import (
    AgentInstanceCreateSerializer,
    AgentInstanceSerializer,
    AgentSettingsUpdateSerializer,
    AgentTemplateSerializer,
)


class AgentTemplateListAPIView(APIView):
    def get(self, request):
        templates = selectors.list_active_templates()
        return Response(AgentTemplateSerializer(templates, many=True).data)


class AgentTemplateDetailAPIView(APIView):
    def get(self, request, template_id):
        template = selectors.get_template_by_id(template_id)
        if not template:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(AgentTemplateSerializer(template).data)


class AgentInstanceListCreateAPIView(APIView):
    def get(self, request):
        if not request.tenant:
            return Response({"detail": "No tenant."}, status=status.HTTP_400_BAD_REQUEST)
        agents = selectors.list_tenant_agents(request.tenant)
        return Response(AgentInstanceSerializer(agents, many=True).data)

    def post(self, request):
        if not request.tenant:
            return Response({"detail": "No tenant."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = AgentInstanceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        template = selectors.get_template_by_id(serializer.validated_data["template_id"])
        if not template:
            return Response({"detail": "Template not found."}, status=status.HTTP_404_NOT_FOUND)
        if not template.is_implemented:
            return Response(
                {"detail": "This agent template is not yet available for deployment."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance = services.create_agent_instance(
            tenant=request.tenant,
            template=template,
            name=serializer.validated_data.get("name") or template.name,
            language=serializer.validated_data.get("language", "en"),
            tone=serializer.validated_data.get("tone", "professional"),
        )
        return Response(
            AgentInstanceSerializer(instance).data,
            status=status.HTTP_201_CREATED,
        )


class AgentInstanceDetailAPIView(APIView):
    def get(self, request, agent_id):
        if not request.tenant:
            return Response({"detail": "No tenant."}, status=status.HTTP_400_BAD_REQUEST)
        instance = selectors.get_tenant_agent(request.tenant, agent_id)
        if not instance:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(AgentInstanceSerializer(instance).data)


class AgentSettingsUpdateAPIView(APIView):
    def patch(self, request, agent_id):
        if not request.tenant:
            return Response({"detail": "No tenant."}, status=status.HTTP_400_BAD_REQUEST)
        instance = selectors.get_tenant_agent(request.tenant, agent_id)
        if not instance:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        settings, _ = AgentSettings.objects.get_or_create(agent_instance=instance)
        serializer = AgentSettingsUpdateSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        instance.refresh_from_db()
        return Response(AgentInstanceSerializer(instance).data)
