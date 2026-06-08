from django.urls import path

from apps.integrations import api_views

urlpatterns = [
    path(
        "integrations/channel-accounts/",
        api_views.ChannelAccountListAPIView.as_view(),
        name="api-channel-accounts",
    ),
    path(
        "integrations/channel-accounts/<int:account_id>/",
        api_views.ChannelAccountDetailAPIView.as_view(),
        name="api-channel-account-detail",
    ),
    path(
        "integrations/channel-accounts/<int:account_id>/test-message/",
        api_views.ChannelTestMessageAPIView.as_view(),
        name="api-channel-test-message",
    ),
    path(
        "integrations/webhook-events/",
        api_views.WebhookEventListAPIView.as_view(),
        name="api-webhook-events",
    ),
]
