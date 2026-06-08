from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.agents.models import AgentInstance
from apps.crm import selectors, services
from apps.crm.models import Contact, Lead
from apps.crm.serializers import (
    ContactSerializer,
    DealSerializer,
    LeadCreateSerializer,
    LeadSerializer,
    LeadUpdateSerializer,
    PipelineStageSerializer,
    TaskCreateSerializer,
    TaskSerializer,
)


def _require_tenant(request):
    if not request.tenant:
        return None, Response({"detail": "No tenant."}, status=status.HTTP_400_BAD_REQUEST)
    return request.tenant, None


class ContactListCreateAPIView(APIView):
    def get(self, request):
        tenant, err = _require_tenant(request)
        if err:
            return err
        contacts = selectors.list_tenant_contacts(tenant)
        return Response(ContactSerializer(contacts, many=True).data)

    def post(self, request):
        tenant, err = _require_tenant(request)
        if err:
            return err
        serializer = ContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact = Contact.objects.create(tenant=tenant, **serializer.validated_data)
        return Response(ContactSerializer(contact).data, status=status.HTTP_201_CREATED)


class LeadListCreateAPIView(APIView):
    def get(self, request):
        tenant, err = _require_tenant(request)
        if err:
            return err
        leads = selectors.list_tenant_leads(tenant)
        status_filter = request.query_params.get("status")
        if status_filter:
            leads = leads.filter(status=status_filter)
        return Response(LeadSerializer(leads, many=True).data)

    def post(self, request):
        tenant, err = _require_tenant(request)
        if err:
            return err
        serializer = LeadCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if data.get("contact_id"):
            contact = Contact.objects.filter(tenant=tenant, pk=data["contact_id"]).first()
            if not contact:
                return Response({"detail": "Contact not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            contact = services.create_contact(
                tenant,
                name=data.get("contact_name", "Unknown"),
                email=data.get("contact_email", ""),
                phone=data.get("contact_phone", ""),
                source=data.get("source", ""),
            )

        agent_instance = None
        if data.get("agent_instance_id"):
            agent_instance = AgentInstance.objects.filter(
                tenant=tenant, pk=data["agent_instance_id"]
            ).first()

        lead = services.create_lead(
            tenant,
            contact,
            title=data["title"],
            agent_instance=agent_instance,
            status=data.get("status", "new"),
            budget=data.get("budget", ""),
            need=data.get("need", ""),
            timeline=data.get("timeline", ""),
            source=data.get("source", ""),
            summary=data.get("summary", ""),
        )
        services.update_lead_score(lead)
        return Response(LeadSerializer(lead).data, status=status.HTTP_201_CREATED)


class LeadDetailAPIView(APIView):
    def get(self, request, lead_id):
        tenant, err = _require_tenant(request)
        if err:
            return err
        lead = selectors.get_tenant_lead(tenant, lead_id)
        if not lead:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(LeadSerializer(lead).data)

    def patch(self, request, lead_id):
        tenant, err = _require_tenant(request)
        if err:
            return err
        lead = selectors.get_tenant_lead(tenant, lead_id)
        if not lead:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = LeadUpdateSerializer(lead, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        services.update_lead_score(lead)
        lead.refresh_from_db()
        return Response(LeadSerializer(lead).data)


class PipelineAPIView(APIView):
    def get(self, request):
        tenant, err = _require_tenant(request)
        if err:
            return err
        services.ensure_default_pipeline_stages(tenant)
        stages = selectors.list_tenant_pipeline_stages(tenant)
        board = selectors.get_pipeline_board(tenant)
        return Response({
            "stages": PipelineStageSerializer(stages, many=True).data,
            "board": [
                {
                    "stage": PipelineStageSerializer(item["stage"]).data,
                    "deals": DealSerializer(item["deals"], many=True).data,
                }
                for item in board
            ],
        })


class TaskCreateAPIView(APIView):
    def post(self, request):
        tenant, err = _require_tenant(request)
        if err:
            return err
        serializer = TaskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        lead = None
        if data.get("lead_id"):
            lead = Lead.objects.filter(tenant=tenant, pk=data["lead_id"]).first()
            if not lead:
                return Response({"detail": "Lead not found."}, status=status.HTTP_404_NOT_FOUND)

        assigned_to = None
        if data.get("assigned_to_id"):
            from apps.accounts.models import User
            assigned_to = User.objects.filter(tenant=tenant, pk=data["assigned_to_id"]).first()

        task = services.create_task(
            tenant,
            title=data["title"],
            lead=lead,
            assigned_to=assigned_to,
            description=data.get("description", ""),
            due_at=data.get("due_at"),
        )
        return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)
