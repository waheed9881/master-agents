from django.urls import path

from apps.knowledge import api_views

urlpatterns = [
    path("knowledge/", api_views.KnowledgeListCreateAPIView.as_view(), name="api-knowledge"),
    path("knowledge/upload/", api_views.KnowledgeUploadAPIView.as_view(), name="api-knowledge-upload"),
]
