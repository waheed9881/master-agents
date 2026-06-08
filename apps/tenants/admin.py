from django.contrib import admin

from apps.tenants.models import Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "country", "industry", "default_currency")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
