"""Agent run logging and tool call tracking."""
from django.db import models


class AgentRun(models.Model):
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="agent_runs",
    )
    agent_instance = models.ForeignKey(
        "agents.AgentInstance",
        on_delete=models.CASCADE,
        related_name="runs",
    )
    conversation = models.ForeignKey(
        "inbox.Conversation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agent_runs",
    )
    input_message = models.TextField()
    output_message = models.TextField(blank=True, default="")
    intent = models.CharField(max_length=128, blank=True, default="")
    confidence = models.FloatField(default=0.0)
    tokens_used = models.PositiveIntegerField(default=0)
    cost_estimate = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Run {self.pk} — {self.intent or 'unknown'}"


class ToolCallStatus(models.TextChoices):
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"
    SKIPPED = "skipped", "Skipped"


class ToolCall(models.Model):
    agent_run = models.ForeignKey(
        AgentRun,
        on_delete=models.CASCADE,
        related_name="tool_calls",
    )
    tool_name = models.CharField(max_length=128)
    input_json = models.JSONField(default=dict, blank=True)
    output_json = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=32,
        choices=ToolCallStatus.choices,
        default=ToolCallStatus.SUCCESS,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.tool_name} ({self.status})"
