from django.urls import path

from apps.inbox import consumers

websocket_urlpatterns = [
    path("ws/inbox/", consumers.InboxConsumer.as_asgi()),
]
