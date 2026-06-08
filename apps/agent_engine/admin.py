from django.contrib import admin

from apps.agent_engine.models import AgentRun, ToolCall


class ToolCallInline(admin.TabularInline):
    model = ToolCall
    extra = 0
    readonly_fields = ("tool_name", "status", "created_at")


@admin.register(AgentRun)
class AgentRunAdmin(admin.ModelAdmin):
    list_display = ("id", "agent_instance", "intent", "confidence", "tokens_used", "created_at")
    list_filter = ("intent", "tenant")
    inlines = [ToolCallInline]


@admin.register(ToolCall)
class ToolCallAdmin(admin.ModelAdmin):
    list_display = ("tool_name", "agent_run", "status", "created_at")
