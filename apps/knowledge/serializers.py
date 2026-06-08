from rest_framework import serializers

from apps.knowledge.models import KnowledgeChunk, KnowledgeSource, KnowledgeSourceType


class KnowledgeChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeChunk
        fields = ("id", "chunk_text", "metadata_json", "created_at")
        read_only_fields = ("id", "created_at")


class KnowledgeSourceSerializer(serializers.ModelSerializer):
    chunk_count = serializers.IntegerField(read_only=True, default=0)
    agent_name = serializers.CharField(source="agent_instance.name", read_only=True, default="")
    source_type_display = serializers.CharField(source="get_source_type_display", read_only=True)

    class Meta:
        model = KnowledgeSource
        fields = (
            "id",
            "agent_instance",
            "agent_name",
            "source_type",
            "source_type_display",
            "title",
            "content",
            "chunk_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class KnowledgeSourceCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    content = serializers.CharField()
    source_type = serializers.ChoiceField(
        choices=KnowledgeSourceType.choices,
        default=KnowledgeSourceType.TEXT,
        required=False,
    )
    agent_instance_id = serializers.IntegerField(required=False)


class KnowledgeUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    source_type = serializers.ChoiceField(
        choices=KnowledgeSourceType.choices,
        default=KnowledgeSourceType.UPLOAD,
        required=False,
    )
    agent_instance_id = serializers.IntegerField(required=False)
