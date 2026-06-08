"""UAT session, checklist, and feedback models."""
from django.conf import settings
from django.db import models
from django.utils import timezone


class UATSessionStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"
    SIGNED_OFF = "signed_off", "Signed Off"
    BLOCKED = "blocked", "Blocked"


class ChecklistItemStatus(models.TextChoices):
    NOT_TESTED = "not_tested", "Not Tested"
    PASSED = "passed", "Passed"
    FAILED = "failed", "Failed"
    BLOCKED = "blocked", "Blocked"
    SKIPPED = "skipped", "Skipped"


class FeedbackCategory(models.TextChoices):
    BUG = "bug", "Bug"
    IMPROVEMENT = "improvement", "Improvement"
    FEATURE_REQUEST = "feature_request", "Feature Request"
    UX = "UX", "UX"
    CONTENT = "content", "Content"
    AGENT_QUALITY = "agent_quality", "Agent Quality"
    SECURITY = "security", "Security"
    PRODUCTION_BLOCKER = "production_blocker", "Production Blocker"
    QUESTION = "question", "Question"


class FeedbackPriority(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"


class FeedbackStatus(models.TextChoices):
    OPEN = "open", "Open"
    TRIAGED = "triaged", "Triaged"
    IN_PROGRESS = "in_progress", "In Progress"
    RESOLVED = "resolved", "Resolved"
    DEFERRED = "deferred", "Deferred"
    REJECTED = "rejected", "Rejected"


class UATSession(models.Model):
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="uat_sessions",
    )
    title = models.CharField(max_length=255)
    demo_version = models.CharField(max_length=64, blank=True, default="MVP 1.8")
    audience = models.CharField(max_length=255, blank=True, default="")
    facilitator = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(
        max_length=32,
        choices=UATSessionStatus.choices,
        default=UATSessionStatus.DRAFT,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    signed_off_at = models.DateTimeField(null=True, blank=True)
    signed_off_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="signed_off_uat_sessions",
    )
    summary = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_uat_sessions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title


class UATChecklistItem(models.Model):
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="uat_checklist_items",
    )
    session = models.ForeignKey(
        UATSession,
        on_delete=models.CASCADE,
        related_name="checklist_items",
    )
    section = models.CharField(max_length=128)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    expected_result = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=32,
        choices=ChecklistItemStatus.choices,
        default=ChecklistItemStatus.NOT_TESTED,
    )
    notes = models.TextField(blank=True, default="")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"{self.section}: {self.title}"


class FeedbackItem(models.Model):
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="feedback_items",
    )
    session = models.ForeignKey(
        UATSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feedback_items",
    )
    source = models.CharField(max_length=128, blank=True, default="uat")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    category = models.CharField(
        max_length=32,
        choices=FeedbackCategory.choices,
        default=FeedbackCategory.IMPROVEMENT,
    )
    priority = models.CharField(
        max_length=16,
        choices=FeedbackPriority.choices,
        default=FeedbackPriority.MEDIUM,
    )
    status = models.CharField(
        max_length=32,
        choices=FeedbackStatus.choices,
        default=FeedbackStatus.OPEN,
    )
    module_area = models.CharField(max_length=64, blank=True, default="")
    related_agent_instance = models.ForeignKey(
        "agents.AgentInstance",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feedback_items",
    )
    related_url = models.CharField(max_length=512, blank=True, default="")
    screenshot_note = models.CharField(max_length=255, blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="feedback_created",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feedback_assigned",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title
