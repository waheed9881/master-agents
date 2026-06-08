from django.urls import path

from apps.integrations import api_views

urlpatterns = [
    path(
        "integrations/channel-accounts/",
        api_views.ChannelAccountListAPIView.as_view(),
        name="api-channel-accounts",
    ),
    path(
        "integrations/webhook-events/",
        api_views.WebhookEventListAPIView.as_view(),
        name="api-webhook-events",
    ),
]
