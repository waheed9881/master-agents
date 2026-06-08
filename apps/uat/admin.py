from django.contrib import admin

from apps.uat.models import FeedbackItem, UATChecklistItem, UATSession


class ChecklistInline(admin.TabularInline):
    model = UATChecklistItem
    extra = 0


@admin.register(UATSession)
class UATSessionAdmin(admin.ModelAdmin):
    list_display = ("title", "tenant", "status", "demo_version", "created_at", "signed_off_at")
    list_filter = ("status", "tenant")
    search_fields = ("title", "audience", "facilitator")
    inlines = [ChecklistInline]


@admin.register(UATChecklistItem)
class UATChecklistItemAdmin(admin.ModelAdmin):
    list_display = ("title", "section", "session", "status", "order")
    list_filter = ("status", "section")


@admin.register(FeedbackItem)
class FeedbackItemAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "priority", "status", "module_area", "tenant", "created_at")
    list_filter = ("category", "priority", "status", "module_area")
