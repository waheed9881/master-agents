"""Unified inbox models for multi-channel messaging."""
from django.db import models


class ChannelType(models.TextChoices):
    WEB_CHAT = "web_chat", "Web Chat"
    WHATSAPP = "whatsapp", "WhatsApp"
    INSTAGRAM = "instagram", "Instagram"


class ChannelAccount(models.Model):
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="channel_accounts",
    )
    channel_type = models.CharField(max_length=32, choices=ChannelType.choices)
    display_name = models.CharField(max_length=255)
    credentials_encrypted = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    mock_mode = models.BooleanField(
        default=True,
        help_text="When enabled, channel uses local mock mode without real Meta API calls.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["channel_type", "display_name"]

    def __str__(self) -> str:
        return f"{self.display_name} ({self.get_channel_type_display()})"


class ConversationStatus(models.TextChoices):
    OPEN = "open", "Open"
    CLOSED = "closed", "Closed"
    ARCHIVED = "archived", "Archived"


class Conversation(models.Model):
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="conversations",
    )
    contact = models.ForeignKey(
        "crm.Contact",
        on_delete=models.CASCADE,
        related_name="conversations",
    )
    agent_instance = models.ForeignKey(
        "agents.AgentInstance",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversations",
    )
    channel_type = models.CharField(max_length=32, choices=ChannelType.choices)
    status = models.CharField(
        max_length=32,
        choices=ConversationStatus.choices,
        default=ConversationStatus.OPEN,
    )
    ai_enabled = models.BooleanField(default=True)
    human_takeover = models.BooleanField(default=False)
    session_key = models.CharField(max_length=128, blank=True, default="", db_index=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_message_at", "-created_at"]

    def __str__(self) -> str:
        return f"{self.contact.name} — {self.get_channel_type_display()}"


class SenderType(models.TextChoices):
    CUSTOMER = "customer", "Customer"
    AI = "ai", "AI"
    HUMAN = "human", "Human"
    SYSTEM = "system", "System"


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender_type = models.CharField(max_length=16, choices=SenderType.choices)
    message_text = models.TextField()
    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.get_sender_type_display()}: {self.message_text[:50]}"
