from django.urls import path

from apps.agent_engine import views

app_name = "agent_engine_settings"

urlpatterns = [
    path("ai-providers/", views.ai_providers_settings_view, name="ai-providers"),
    path("ai-providers/test/", views.ai_providers_test_view, name="ai-providers-test"),
]
