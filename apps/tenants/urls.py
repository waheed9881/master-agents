from django.urls import path

from apps.tenants import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard_view, name="index"),
]
