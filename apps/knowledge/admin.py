from django.contrib import admin

from apps.knowledge.models import KnowledgeChunk, KnowledgeSource


class KnowledgeChunkInline(admin.TabularInline):
    model = KnowledgeChunk
    extra = 0
    readonly_fields = ("chunk_text", "created_at")


@admin.register(KnowledgeSource)
class KnowledgeSourceAdmin(admin.ModelAdmin):
    list_display = ("title", "source_type", "tenant", "agent_instance", "updated_at")
    list_filter = ("source_type", "tenant")
    search_fields = ("title", "content")
    inlines = [KnowledgeChunkInline]


@admin.register(KnowledgeChunk)
class KnowledgeChunkAdmin(admin.ModelAdmin):
    list_display = ("source", "tenant", "created_at")
    list_filter = ("tenant",)
    search_fields = ("chunk_text", "source__title")
