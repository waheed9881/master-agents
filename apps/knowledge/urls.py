from django.urls import path

from apps.knowledge import views

app_name = "knowledge"

urlpatterns = [
    path("", views.knowledge_list_view, name="list"),
    path("sources/<int:source_id>/", views.knowledge_source_detail_view, name="source_detail"),
]
