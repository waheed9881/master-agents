from django.urls import path

from apps.inbox import api_views

urlpatterns = [
    path("conversations/", api_views.ConversationListAPIView.as_view(), name="api-conversations"),
    path(
        "conversations/<int:conversation_id>/",
        api_views.ConversationDetailAPIView.as_view(),
        name="api-conversation-detail",
    ),
    path(
        "conversations/<int:conversation_id>/messages/",
        api_views.ConversationSendMessageAPIView.as_view(),
        name="api-conversation-messages",
    ),
    path(
        "conversations/<int:conversation_id>/human-takeover/",
        api_views.HumanTakeoverAPIView.as_view(),
        name="api-human-takeover",
    ),
    path(
        "conversations/<int:conversation_id>/enable-ai/",
        api_views.EnableAIAPIView.as_view(),
        name="api-enable-ai",
    ),
    path("webchat/message/", api_views.WebChatMessageAPIView.as_view(), name="api-webchat-message"),
]
