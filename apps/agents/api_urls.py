from django.urls import path

from apps.agents import api_views

urlpatterns = [
    path("agent-templates/", api_views.AgentTemplateListAPIView.as_view(), name="api-agent-templates"),
    path(
        "agent-templates/<int:template_id>/",
        api_views.AgentTemplateDetailAPIView.as_view(),
        name="api-agent-template-detail",
    ),
    path("agents/", api_views.AgentInstanceListCreateAPIView.as_view(), name="api-agents"),
    path(
        "agents/<int:agent_id>/",
        api_views.AgentInstanceDetailAPIView.as_view(),
        name="api-agent-detail",
    ),
    path(
        "agents/<int:agent_id>/settings/",
        api_views.AgentSettingsUpdateAPIView.as_view(),
        name="api-agent-settings",
    ),
]
