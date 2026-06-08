"""Agent templates and tenant-scoped agent instances."""
from django.db import models


class AgentTemplate(models.Model):
    """Catalog template for a deployable AI agent type."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()
    category = models.CharField(max_length=128)
    priority_label = models.CharField(max_length=64, blank=True, default="")
    market_need_score = models.PositiveSmallIntegerField(default=0)
    tags_json = models.JSONField(default=list, blank=True)
    default_workflow_json = models.JSONField(default=dict, blank=True)
    default_prompt = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    is_implemented = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-market_need_score", "name"]

    def __str__(self) -> str:
        return self.name


class AgentInstanceStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    PAUSED = "paused", "Paused"
    ARCHIVED = "archived", "Archived"


class AgentInstance(models.Model):
    """Tenant-deployed agent based on a template."""

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="agent_instances",
    )
    template = models.ForeignKey(
        AgentTemplate,
        on_delete=models.PROTECT,
        related_name="instances",
    )
    name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=32,
        choices=AgentInstanceStatus.choices,
        default=AgentInstanceStatus.DRAFT,
    )
    language = models.CharField(max_length=16, default="en")
    tone = models.CharField(max_length=64, default="professional")
    ai_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("tenant", "template", "name")]

    def __str__(self) -> str:
        return f"{self.name} ({self.tenant.name})"


class AgentSettings(models.Model):
    """Business configuration for an agent instance."""

    agent_instance = models.OneToOneField(
        AgentInstance,
        on_delete=models.CASCADE,
        related_name="settings",
    )
    business_name = models.CharField(max_length=255, blank=True, default="")
    business_description = models.TextField(blank=True, default="")
    services_json = models.JSONField(default=list, blank=True)
    pricing_json = models.JSONField(default=dict, blank=True)
    qualification_questions_json = models.JSONField(default=list, blank=True)
    objection_handling_json = models.JSONField(default=dict, blank=True)
    handoff_rules_json = models.JSONField(default=dict, blank=True)
    working_hours_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Agent settings"

    def __str__(self) -> str:
        return f"Settings for {self.agent_instance.name}"
