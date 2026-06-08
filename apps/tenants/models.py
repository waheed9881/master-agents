"""Multi-tenant workspace models."""
from django.db import models
from django.utils.text import slugify


class Tenant(models.Model):
    """Company / workspace."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    country = models.CharField(max_length=64, blank=True, default="")
    industry = models.CharField(max_length=128, blank=True, default="")
    timezone = models.CharField(max_length=64, default="UTC")
    default_currency = models.CharField(max_length=8, default="USD")
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
