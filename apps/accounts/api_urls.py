from django.urls import path

from apps.accounts import api_views

urlpatterns = [
    path("auth/login/", api_views.LoginAPIView.as_view(), name="api-login"),
    path("auth/logout/", api_views.LogoutAPIView.as_view(), name="api-logout"),
    path("me/", api_views.MeAPIView.as_view(), name="api-me"),
]
