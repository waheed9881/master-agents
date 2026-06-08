"""CRM models: contacts, leads, pipeline, deals, tasks."""
from django.conf import settings
from django.db import models


class Contact(models.Model):
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="contacts",
    )
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=32, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    city = models.CharField(max_length=128, blank=True, default="")
    country = models.CharField(max_length=64, blank=True, default="")
    source = models.CharField(max_length=128, blank=True, default="")
    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name


class LeadStatus(models.TextChoices):
    NEW = "new", "New"
    QUALIFYING = "qualifying", "Qualifying"
    QUALIFIED = "qualified", "Qualified"
    HOT = "hot", "Hot"
    DEMO_BOOKED = "demo_booked", "Demo Booked"
    WON = "won", "Won"
    LOST = "lost", "Lost"


class Lead(models.Model):
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="leads",
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name="leads",
    )
    agent_instance = models.ForeignKey(
        "agents.AgentInstance",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leads",
    )
    title = models.CharField(max_length=255)
    status = models.CharField(
        max_length=32,
        choices=LeadStatus.choices,
        default=LeadStatus.NEW,
    )
    score = models.PositiveSmallIntegerField(default=0)
    budget = models.CharField(max_length=128, blank=True, default="")
    need = models.TextField(blank=True, default="")
    timeline = models.CharField(max_length=128, blank=True, default="")
    source = models.CharField(max_length=128, blank=True, default="")
    summary = models.TextField(blank=True, default="")
    next_follow_up_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.title


class PipelineStage(models.Model):
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="pipeline_stages",
    )
    name = models.CharField(max_length=128)
    order = models.PositiveSmallIntegerField(default=0)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        unique_together = [("tenant", "name")]

    def __str__(self) -> str:
        return f"{self.name} ({self.tenant.name})"


class Deal(models.Model):
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="deals",
    )
    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name="deals",
    )
    stage = models.ForeignKey(
        PipelineStage,
        on_delete=models.PROTECT,
        related_name="deals",
    )
    value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=8, default="USD")
    probability = models.PositiveSmallIntegerField(default=0)
    expected_close_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"Deal: {self.lead.title} — {self.value} {self.currency}"


class TaskStatus(models.TextChoices):
    OPEN = "open", "Open"
    IN_PROGRESS = "in_progress", "In Progress"
    DONE = "done", "Done"
    CANCELLED = "cancelled", "Cancelled"


class Task(models.Model):
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name="tasks",
        null=True,
        blank=True,
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    due_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=32,
        choices=TaskStatus.choices,
        default=TaskStatus.OPEN,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["due_at", "-created_at"]

    def __str__(self) -> str:
        return self.title
