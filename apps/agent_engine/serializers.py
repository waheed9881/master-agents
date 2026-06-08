from rest_framework import serializers


class TestMessageSerializer(serializers.Serializer):
    message_text = serializers.CharField()
    agent_instance_id = serializers.IntegerField()
    customer_name = serializers.CharField(required=False, default="Test Customer")
    customer_email = serializers.EmailField(required=False, allow_blank=True, default="")
    session_key = serializers.CharField(required=False, allow_blank=True, default="")


class ProviderTestSerializer(serializers.Serializer):
    message_text = serializers.CharField()
    agent_instance_id = serializers.IntegerField()
    provider = serializers.CharField(required=False, default="mock")
