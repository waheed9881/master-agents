from django.urls import path

from apps.crm import api_views

urlpatterns = [
    path("contacts/", api_views.ContactListCreateAPIView.as_view(), name="api-contacts"),
    path("leads/", api_views.LeadListCreateAPIView.as_view(), name="api-leads"),
    path("leads/<int:lead_id>/", api_views.LeadDetailAPIView.as_view(), name="api-lead-detail"),
    path("pipeline/", api_views.PipelineAPIView.as_view(), name="api-pipeline"),
    path("tasks/", api_views.TaskCreateAPIView.as_view(), name="api-tasks"),
]
