from rest_framework import serializers

from apps.inbox.models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ("id", "sender_type", "message_text", "metadata_json", "created_at")


class ConversationListSerializer(serializers.ModelSerializer):
    contact_name = serializers.CharField(source="contact.name", read_only=True)
    contact_email = serializers.CharField(source="contact.email", read_only=True)
    agent_name = serializers.CharField(source="agent_instance.name", read_only=True, default=None)
    last_message = serializers.SerializerMethodField()
    message_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Conversation
        fields = (
            "id", "contact", "contact_name", "contact_email",
            "agent_instance", "agent_name", "channel_type", "status",
            "ai_enabled", "human_takeover", "last_message_at",
            "last_message", "message_count", "created_at",
        )

    def get_last_message(self, obj):
        msg = obj.messages.order_by("-created_at").first()
        if msg:
            return MessageSerializer(msg).data
        return None


class ConversationDetailSerializer(serializers.ModelSerializer):
    contact_name = serializers.CharField(source="contact.name", read_only=True)
    contact_email = serializers.CharField(source="contact.email", read_only=True)
    contact_phone = serializers.CharField(source="contact.phone", read_only=True)
    agent_name = serializers.CharField(source="agent_instance.name", read_only=True, default=None)
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = (
            "id", "contact", "contact_name", "contact_email", "contact_phone",
            "agent_instance", "agent_name", "channel_type", "status",
            "ai_enabled", "human_takeover", "session_key", "last_message_at",
            "messages", "created_at", "updated_at",
        )


class SendMessageSerializer(serializers.Serializer):
    message_text = serializers.CharField()


class WebChatMessageSerializer(serializers.Serializer):
    message_text = serializers.CharField()
    customer_name = serializers.CharField(required=False, default="Web Chat Visitor")
    customer_email = serializers.EmailField(required=False, allow_blank=True, default="")
    customer_phone = serializers.CharField(required=False, allow_blank=True, default="")
    agent_instance_id = serializers.IntegerField(required=False)
    session_key = serializers.CharField(required=False, allow_blank=True, default="")
