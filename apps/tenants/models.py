"""Multi-tenant workspace models."""
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Tenant(models.Model):
    """Company / workspace."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    country = models.CharField(max_length=64, blank=True, default="")
    industry = models.CharField(max_length=128, blank=True, default="")
    timezone = models.CharField(max_length=64, default="UTC")
    default_currency = models.CharField(max_length=8, default="USD")
    business_description = models.TextField(blank=True, default="")
    support_email = models.EmailField(blank=True, default="")
    support_phone = models.CharField(max_length=32, blank=True, default="")
    onboarding_step = models.PositiveSmallIntegerField(default=0)
    onboarding_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "tenant"
            slug = base
            counter = 1
            while Tenant.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Plan(models.Model):
    """SaaS plan with usage limits (local/demo billing — no payment gateway)."""

    name = models.CharField(max_length=64)
    slug = models.SlugField(max_length=64, unique=True)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=8, default="USD")
    max_agents = models.PositiveIntegerField(default=1)
    max_team_members = models.PositiveIntegerField(default=3)
    max_monthly_messages = models.PositiveIntegerField(default=1000)
    max_knowledge_sources = models.PositiveIntegerField(default=10)
    max_integrations = models.PositiveIntegerField(default=1)
    allow_real_ai_provider = models.BooleanField(default=False)
    allow_whatsapp = models.BooleanField(default=False)
    allow_instagram = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["monthly_price"]

    def __str__(self) -> str:
        return self.name


class SubscriptionStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    TRIAL = "trial", "Trial"
    CANCELLED = "cancelled", "Cancelled"


class TenantSubscription(models.Model):
    """Tenant plan subscription (local assignment only)."""

    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.CASCADE,
        related_name="subscription",
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )
    status = models.CharField(
        max_length=32,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE,
    )
    current_period_start = models.DateTimeField(default=timezone.now)
    current_period_end = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.tenant.name} — {self.plan.name}"
