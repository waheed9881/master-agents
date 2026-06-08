from django.contrib import admin

from apps.crm.models import Contact, Deal, Lead, PipelineStage, Task


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "tenant", "source", "created_at")
    list_filter = ("tenant", "source")
    search_fields = ("name", "email", "phone")


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("title", "contact", "status", "score", "tenant", "updated_at")
    list_filter = ("status", "tenant")
    search_fields = ("title", "contact__name")


@admin.register(PipelineStage)
class PipelineStageAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "order", "is_default")
    list_filter = ("tenant",)
    ordering = ("tenant", "order")


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ("lead", "stage", "value", "currency", "probability", "tenant")
    list_filter = ("tenant", "stage")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "lead", "assigned_to", "status", "due_at", "tenant")
    list_filter = ("status", "tenant")
