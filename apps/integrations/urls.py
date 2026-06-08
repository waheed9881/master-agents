from django.urls import path

from apps.integrations import views

app_name = "integrations"

urlpatterns = [
    path("", views.integrations_index_view, name="index"),
    path("channels/new/", views.channel_create_view, name="channel_create"),
    path("channels/<int:channel_id>/edit/", views.channel_edit_view, name="channel_edit"),
    path("channels/<int:channel_id>/toggle/", views.channel_toggle_view, name="channel_toggle"),
    path("channels/<int:channel_id>/test/", views.channel_test_view, name="channel_test"),
    path("webhook-events/", views.webhook_events_view, name="webhook_events"),
]
