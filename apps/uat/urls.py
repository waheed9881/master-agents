from django.urls import path

from apps.uat import views

app_name = "uat"

urlpatterns = [
    path("", views.uat_dashboard_view, name="dashboard"),
    path("sessions/", views.session_list_view, name="session-list"),
    path("sessions/new/", views.session_create_view, name="session-create"),
    path("sessions/<int:session_id>/", views.session_detail_view, name="session-detail"),
    path("sessions/<int:session_id>/checklist/add/", views.checklist_add_view, name="checklist-add"),
    path("feedback/", views.feedback_list_view, name="feedback-list"),
    path("feedback/new/", views.feedback_create_view, name="feedback-create"),
    path("feedback/export.csv", views.feedback_export_csv_view, name="feedback-export"),
    path("feedback/<int:item_id>/edit/", views.feedback_edit_view, name="feedback-edit"),
    path("report/", views.uat_report_view, name="report"),
]
