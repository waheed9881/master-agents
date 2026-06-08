from django.urls import path

from apps.accounts import onboarding_views, views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("onboarding/", onboarding_views.onboarding_view, name="onboarding"),
]
