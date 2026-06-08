from rest_framework import serializers

from apps.crm.models import Contact, Deal, Lead, LeadStatus, PipelineStage, Task


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = (
            "id", "name", "phone", "email", "city", "country",
            "source", "metadata_json", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class LeadSerializer(serializers.ModelSerializer):
    contact_name = serializers.CharField(source="contact.name", read_only=True)
    contact_email = serializers.CharField(source="contact.email", read_only=True)
    contact_phone = serializers.CharField(source="contact.phone", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Lead
        fields = (
            "id", "contact", "contact_name", "contact_email", "contact_phone",
            "agent_instance", "title", "status", "status_display", "score",
            "budget", "need", "timeline", "source", "summary",
            "next_follow_up_at", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class LeadCreateSerializer(serializers.Serializer):
    contact_id = serializers.IntegerField(required=False)
    contact_name = serializers.CharField(max_length=255, required=False)
    contact_email = serializers.EmailField(required=False, allow_blank=True)
    contact_phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    title = serializers.CharField(max_length=255)
    status = serializers.ChoiceField(choices=LeadStatus.choices, required=False)
    budget = serializers.CharField(max_length=128, required=False, allow_blank=True)
    need = serializers.CharField(required=False, allow_blank=True)
    timeline = serializers.CharField(max_length=128, required=False, allow_blank=True)
    source = serializers.CharField(max_length=128, required=False, allow_blank=True)
    summary = serializers.CharField(required=False, allow_blank=True)
    agent_instance_id = serializers.IntegerField(required=False)


class LeadUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = (
            "title", "status", "score", "budget", "need", "timeline",
            "source", "summary", "next_follow_up_at", "agent_instance",
        )


class PipelineStageSerializer(serializers.ModelSerializer):
    deal_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = PipelineStage
        fields = ("id", "name", "order", "is_default", "deal_count", "created_at")


class DealSerializer(serializers.ModelSerializer):
    lead_title = serializers.CharField(source="lead.title", read_only=True)
    contact_name = serializers.CharField(source="lead.contact.name", read_only=True)
    stage_name = serializers.CharField(source="stage.name", read_only=True)

    class Meta:
        model = Deal
        fields = (
            "id", "lead", "lead_title", "contact_name", "stage", "stage_name",
            "value", "currency", "probability", "expected_close_date",
            "created_at", "updated_at",
        )


class TaskSerializer(serializers.ModelSerializer):
    lead_title = serializers.CharField(source="lead.title", read_only=True, default=None)

    class Meta:
        model = Task
        fields = (
            "id", "lead", "lead_title", "assigned_to", "title", "description",
            "due_at", "status", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class TaskCreateSerializer(serializers.Serializer):
    lead_id = serializers.IntegerField(required=False)
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    due_at = serializers.DateTimeField(required=False)
    assigned_to_id = serializers.IntegerField(required=False)
