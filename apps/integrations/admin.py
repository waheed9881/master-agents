from django.contrib import admin

from apps.integrations.models import ChannelCredential, WebhookEvent


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = (
        "channel_type",
        "processing_status",
        "external_message_id",
        "tenant",
        "received_at",
    )
    list_filter = ("channel_type", "processing_status", "tenant")
    search_fields = ("external_message_id", "external_event_id")
    readonly_fields = ("received_at", "created_at", "processed_at")


@admin.register(ChannelCredential)
class ChannelCredentialAdmin(admin.ModelAdmin):
    list_display = (
        "channel_account",
        "tenant",
        "provider",
        "phone_number_id",
        "page_id",
        "is_active",
    )
    list_filter = ("provider", "is_active", "tenant")
