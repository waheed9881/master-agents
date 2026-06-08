from django.urls import path

from apps.inbox import views

app_name = "inbox"

urlpatterns = [
    path("", views.inbox_list_view, name="list"),
    path("webchat/", views.webchat_demo_view, name="webchat_demo"),
    path("<int:conversation_id>/", views.conversation_detail_view, name="detail"),
]
