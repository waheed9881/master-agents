from django.urls import path

from apps.integrations import views

app_name = "integrations"

urlpatterns = [
    path("", views.integrations_index_view, name="index"),
]
