"""Integration models for webhooks and channel credentials."""
from django.db import models


class WebhookProcessingStatus(models.TextChoices):
    RECEIVED = "received", "Received"
    IGNORED = "ignored", "Ignored"
    PROCESSED = "processed", "Processed"
    FAILED = "failed", "Failed"
    DUPLICATE = "duplicate", "Duplicate"


class WebhookEvent(models.Model):
    """Audit log for inbound webhook payloads."""

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="webhook_events",
    )
    channel_type = models.CharField(max_length=32)
    external_event_id = models.CharField(max_length=255, blank=True, default="")
    external_message_id = models.CharField(max_length=255, blank=True, default="", db_index=True)
    event_type = models.CharField(max_length=128, blank=True, default="")
    payload_json = models.JSONField(default=dict, blank=True)
    normalized_json = models.JSONField(default=dict, blank=True)
    processing_status = models.CharField(
        max_length=32,
        choices=WebhookProcessingStatus.choices,
        default=WebhookProcessingStatus.RECEIVED,
    )
    error_message = models.TextField(blank=True, default="")
    conversation = models.ForeignKey(
        "inbox.Conversation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="webhook_events",
    )
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-received_at"]

    def __str__(self) -> str:
        return f"{self.channel_type} {self.processing_status} ({self.external_message_id or self.pk})"


class ChannelCredential(models.Model):
    """Meta/WhatsApp/Instagram credentials linked to a channel account."""

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="channel_credentials",
    )
    channel_account = models.OneToOneField(
        "inbox.ChannelAccount",
        on_delete=models.CASCADE,
        related_name="credential",
    )
    provider = models.CharField(max_length=64, default="meta")
    app_id = models.CharField(max_length=128, blank=True, default="")
    page_id = models.CharField(max_length=128, blank=True, default="", db_index=True)
    business_account_id = models.CharField(max_length=128, blank=True, default="")
    phone_number_id = models.CharField(max_length=128, blank=True, default="", db_index=True)
    access_token_encrypted = models.TextField(blank=True, default="")
    verify_token = models.CharField(max_length=255, blank=True, default="")
    app_secret_encrypted = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["channel_account__channel_type"]

    def __str__(self) -> str:
        return f"{self.channel_account.display_name} ({self.provider})"
