from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.services import AnalyticsService


def _require_tenant(request):
    if not request.tenant:
        return None, Response({"detail": "No tenant."}, status=status.HTTP_400_BAD_REQUEST)
    return request.tenant, None


def _get_range(request) -> str:
    return request.query_params.get("range", "last_30_days")


class AnalyticsOverviewAPIView(APIView):
    def get(self, request):
        tenant, err = _require_tenant(request)
        if err:
            return err
        return Response(AnalyticsService.get_overview_metrics(tenant, _get_range(request)))


class AnalyticsFunnelAPIView(APIView):
    def get(self, request):
        tenant, err = _require_tenant(request)
        if err:
            return err
        return Response(AnalyticsService.get_conversion_funnel(tenant, _get_range(request)))


class AnalyticsAgentsAPIView(APIView):
    def get(self, request):
        tenant, err = _require_tenant(request)
        if err:
            return err
        return Response(AnalyticsService.get_agent_performance(tenant, _get_range(request)))


class AnalyticsInboxAPIView(APIView):
    def get(self, request):
        tenant, err = _require_tenant(request)
        if err:
            return err
        return Response(AnalyticsService.get_inbox_metrics(tenant, _get_range(request)))


class AnalyticsKnowledgeAPIView(APIView):
    def get(self, request):
        tenant, err = _require_tenant(request)
        if err:
            return err
        return Response(AnalyticsService.get_knowledge_metrics(tenant, _get_range(request)))


class AnalyticsRecentActivityAPIView(APIView):
    def get(self, request):
        tenant, err = _require_tenant(request)
        if err:
            return err
        return Response(AnalyticsService.get_recent_activity(tenant, _get_range(request)))
