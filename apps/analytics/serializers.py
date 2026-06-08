"""DRF serializers for analytics API responses."""
from rest_framework import serializers


class FunnelStageSerializer(serializers.Serializer):
    status = serializers.CharField()
    label = serializers.CharField()
    count = serializers.IntegerField()
    percentage = serializers.FloatField()


class SourceBreakdownSerializer(serializers.Serializer):
    source = serializers.CharField()
    label = serializers.CharField()
    count = serializers.IntegerField()
    percentage = serializers.FloatField()


class AgentPerformanceSerializer(serializers.Serializer):
    agent_id = serializers.IntegerField()
    agent_name = serializers.CharField()
    template_name = serializers.CharField()
    total_conversations = serializers.IntegerField()
    total_leads = serializers.IntegerField()
    hot_leads = serializers.IntegerField()
    average_lead_score = serializers.FloatField()
    agent_runs = serializers.IntegerField()
    human_handoffs = serializers.IntegerField()
    knowledge_sources = serializers.IntegerField()
