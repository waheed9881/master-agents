from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.agents.models import AgentInstance
from apps.knowledge import selectors, services
from apps.knowledge.serializers import (
    KnowledgeSourceCreateSerializer,
    KnowledgeSourceSerializer,
    KnowledgeUploadSerializer,
)


def _require_tenant(request):
    if not request.tenant:
        return None, Response({"detail": "No tenant."}, status=status.HTTP_400_BAD_REQUEST)
    return request.tenant, None


def _resolve_agent(tenant, agent_instance_id: int | None):
    if not agent_instance_id:
        return None, None
    agent = AgentInstance.objects.filter(tenant=tenant, pk=agent_instance_id).first()
    if not agent:
        return None, Response({"detail": "Agent instance not found."}, status=status.HTTP_404_NOT_FOUND)
    return agent, None


class KnowledgeListCreateAPIView(APIView):
    parser_classes = [JSONParser, FormParser]

    def get(self, request):
        tenant, err = _require_tenant(request)
        if err:
            return err

        agent_id = request.query_params.get("agent_instance_id")
        sources = selectors.list_tenant_knowledge_sources(
            tenant,
            agent_instance_id=int(agent_id) if agent_id else None,
        )
        return Response(KnowledgeSourceSerializer(sources, many=True).data)

    def post(self, request):
        tenant, err = _require_tenant(request)
        if err:
            return err

        serializer = KnowledgeSourceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        agent, agent_err = _resolve_agent(tenant, data.get("agent_instance_id"))
        if agent_err:
            return agent_err

        source = services.create_knowledge_source(
            tenant,
            title=data["title"],
            content=data["content"],
            source_type=data.get("source_type", "text"),
            agent_instance=agent,
        )
        source = selectors.list_tenant_knowledge_sources(tenant).get(pk=source.pk)
        return Response(KnowledgeSourceSerializer(source).data, status=status.HTTP_201_CREATED)


class KnowledgeUploadAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        tenant, err = _require_tenant(request)
        if err:
            return err

        serializer = KnowledgeUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        uploaded = data["file"]
        try:
            raw = uploaded.read()
            content = raw.decode("utf-8")
        except UnicodeDecodeError:
            return Response(
                {"detail": "File must be UTF-8 encoded text."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not content.strip():
            return Response({"detail": "File is empty."}, status=status.HTTP_400_BAD_REQUEST)

        agent, agent_err = _resolve_agent(tenant, data.get("agent_instance_id"))
        if agent_err:
            return agent_err

        title = data.get("title") or uploaded.name
        source = services.create_knowledge_source(
            tenant,
            title=title,
            content=content,
            source_type=data.get("source_type", "upload"),
            agent_instance=agent,
        )
        source = selectors.list_tenant_knowledge_sources(tenant).get(pk=source.pk)
        return Response(KnowledgeSourceSerializer(source).data, status=status.HTTP_201_CREATED)
