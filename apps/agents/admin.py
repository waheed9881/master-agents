from django.contrib import admin

from apps.agents.models import AgentInstance, AgentSettings, AgentTemplate


@admin.register(AgentTemplate)
class AgentTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "category",
        "priority_label",
        "market_need_score",
        "is_implemented",
        "is_active",
    )
    list_filter = ("is_implemented", "is_active", "category")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}


class AgentSettingsInline(admin.StackedInline):
    model = AgentSettings
    extra = 0


@admin.register(AgentInstance)
class AgentInstanceAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "template", "status", "ai_enabled", "created_at")
    list_filter = ("status", "ai_enabled", "template")
    search_fields = ("name", "tenant__name")
    inlines = [AgentSettingsInline]


@admin.register(AgentSettings)
class AgentSettingsAdmin(admin.ModelAdmin):
    list_display = ("agent_instance", "business_name", "updated_at")
    search_fields = ("business_name", "agent_instance__name")
