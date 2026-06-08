from django.urls import path

from apps.demo import views

app_name = "demo"

urlpatterns = [
    path("", views.demo_center_view, name="center"),
    path("report/", views.demo_report_view, name="report"),
]
