from django.urls import path

from apps.integrations.webhooks import instagram, whatsapp

urlpatterns = [
    path("whatsapp/", whatsapp.whatsapp_webhook, name="webhook-whatsapp"),
    path("instagram/", instagram.instagram_webhook, name="webhook-instagram"),
]
