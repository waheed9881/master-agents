"""Knowledge base models for agent answers."""
from django.db import models


class KnowledgeSourceType(models.TextChoices):
    TEXT = "text", "Text"
    FAQ = "faq", "FAQ"
    PRICING = "pricing", "Pricing"
    POLICY = "policy", "Policy"
    UPLOAD = "upload", "Upload"
    URL = "url", "URL"


class KnowledgeSource(models.Model):
    """A document or entry in the tenant knowledge base."""

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="knowledge_sources",
    )
    agent_instance = models.ForeignKey(
        "agents.AgentInstance",
        on_delete=models.CASCADE,
        related_name="knowledge_sources",
        null=True,
        blank=True,
    )
    source_type = models.CharField(
        max_length=32,
        choices=KnowledgeSourceType.choices,
        default=KnowledgeSourceType.TEXT,
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.title


class KnowledgeChunk(models.Model):
    """Searchable chunk derived from a knowledge source."""

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="knowledge_chunks",
    )
    source = models.ForeignKey(
        KnowledgeSource,
        on_delete=models.CASCADE,
        related_name="chunks",
    )
    chunk_text = models.TextField()
    # pgvector-ready: store embedding as JSON until VectorField is enabled
    embedding = models.JSONField(default=list, blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["source", "pk"]

    def __str__(self) -> str:
        return f"Chunk {self.pk} ({self.source.title})"
