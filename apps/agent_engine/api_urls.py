from django.urls import path

from apps.agent_engine import api_views

urlpatterns = [
    path("agent-engine/test-message/", api_views.TestMessageAPIView.as_view(), name="api-agent-test-message"),
    path("agent-engine/providers/status/", api_views.ProviderStatusAPIView.as_view(), name="api-provider-status"),
    path("agent-engine/providers/test/", api_views.ProviderTestAPIView.as_view(), name="api-provider-test"),
]
