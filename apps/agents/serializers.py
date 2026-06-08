from rest_framework import serializers

from apps.agents.models import AgentInstance, AgentSettings, AgentTemplate


class AgentTemplateSerializer(serializers.ModelSerializer):
    region_tags = serializers.SerializerMethodField()
    implementation_progress = serializers.SerializerMethodField()

    class Meta:
        model = AgentTemplate
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "category",
            "priority_label",
            "market_need_score",
            "tags_json",
            "region_tags",
            "default_workflow_json",
            "default_prompt",
            "is_active",
            "is_implemented",
            "implementation_progress",
            "created_at",
            "updated_at",
        )

    def get_region_tags(self, obj: AgentTemplate) -> list[str]:
        tags = obj.tags_json or []
        regions = {"PK", "KSA", "USA", "UAE", "Global"}
        return [t for t in tags if t in regions]

    def get_implementation_progress(self, obj: AgentTemplate) -> int:
        return 100 if obj.is_implemented else 15


class AgentSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentSettings
        fields = (
            "business_name",
            "business_description",
            "services_json",
            "pricing_json",
            "qualification_questions_json",
            "objection_handling_json",
            "handoff_rules_json",
            "working_hours_json",
        )


class AgentInstanceSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source="template.name", read_only=True)
    template_slug = serializers.CharField(source="template.slug", read_only=True)
    settings = AgentSettingsSerializer(read_only=True)

    class Meta:
        model = AgentInstance
        fields = (
            "id",
            "tenant",
            "template",
            "template_name",
            "template_slug",
            "name",
            "status",
            "language",
            "tone",
            "ai_enabled",
            "settings",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("tenant",)


class AgentInstanceCreateSerializer(serializers.Serializer):
    template_id = serializers.IntegerField()
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    language = serializers.CharField(max_length=16, required=False, default="en")
    tone = serializers.CharField(max_length=64, required=False, default="professional")


class AgentSettingsUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentSettings
        fields = (
            "business_name",
            "business_description",
            "services_json",
            "pricing_json",
            "qualification_questions_json",
            "objection_handling_json",
            "handoff_rules_json",
            "working_hours_json",
        )
