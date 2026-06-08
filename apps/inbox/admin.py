from django.contrib import admin

from apps.inbox.models import ChannelAccount, Conversation, Message


@admin.register(ChannelAccount)
class ChannelAccountAdmin(admin.ModelAdmin):
    list_display = ("display_name", "channel_type", "tenant", "is_active")
    list_filter = ("channel_type", "is_active", "tenant")


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("sender_type", "message_text", "created_at")


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = (
        "contact",
        "channel_type",
        "status",
        "ai_enabled",
        "human_takeover",
        "last_message_at",
        "tenant",
    )
    list_filter = ("channel_type", "status", "ai_enabled", "human_takeover", "tenant")
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "sender_type", "message_text", "created_at")
    list_filter = ("sender_type",)
