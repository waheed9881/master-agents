from django.urls import path

from apps.crm import views

app_name = "crm"

urlpatterns = [
    path("leads/", views.leads_list_view, name="leads"),
    path("leads/<int:lead_id>/", views.lead_detail_view, name="lead_detail"),
    path("pipeline/", views.pipeline_board_view, name="pipeline"),
]
