from django.contrib import admin

from apps.tenants.models import AuditLog, Plan, Tenant, TenantSubscription


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "country", "industry", "onboarding_completed", "created_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "monthly_price", "max_agents", "is_active")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(TenantSubscription)
class TenantSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("tenant", "plan", "status", "current_period_start", "current_period_end")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "user", "tenant", "object_type", "object_id")
    list_filter = ("action", "object_type")
    search_fields = ("action", "object_id", "user__email")
    readonly_fields = ("created_at",)
