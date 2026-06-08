from django.urls import path

from apps.agents import views

app_name = "agents"

urlpatterns = [
    path("", views.agent_gallery_view, name="gallery"),
    path("instances/<int:agent_id>/", views.agent_instance_detail_view, name="instance_detail"),
    path("templates/<slug:slug>/deploy/", views.deploy_agent_view, name="deploy"),
    path("templates/<slug:slug>/", views.agent_template_detail_view, name="detail"),
]
