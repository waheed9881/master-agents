from django.urls import path

from apps.analytics import api_views

urlpatterns = [
    path("analytics/overview/", api_views.AnalyticsOverviewAPIView.as_view(), name="api-analytics-overview"),
    path("analytics/funnel/", api_views.AnalyticsFunnelAPIView.as_view(), name="api-analytics-funnel"),
    path("analytics/agents/", api_views.AnalyticsAgentsAPIView.as_view(), name="api-analytics-agents"),
    path("analytics/inbox/", api_views.AnalyticsInboxAPIView.as_view(), name="api-analytics-inbox"),
    path("analytics/knowledge/", api_views.AnalyticsKnowledgeAPIView.as_view(), name="api-analytics-knowledge"),
    path(
        "analytics/recent-activity/",
        api_views.AnalyticsRecentActivityAPIView.as_view(),
        name="api-analytics-recent-activity",
    ),
]
