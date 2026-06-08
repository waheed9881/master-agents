"""Management command to reset demo operational data safely."""
from django.core.management.base import BaseCommand

from apps.tenants.demo_reset import reset_safe_demo_data
from apps.tenants.models import Tenant


class Command(BaseCommand):
    help = "Reset demo conversations, CRM, agent runs, and webhooks. Keeps tenant/users/agents."

    def add_arguments(self, parser):
        parser.add_argument(
            "--safe",
            action="store_true",
            help="Safe reset: clear operational data, keep tenant/users/agents/knowledge.",
        )
        parser.add_argument(
            "--reseed",
            action="store_true",
            help="Re-seed CRM and inbox demo data after reset.",
        )
        parser.add_argument(
            "--tenant-slug",
            default="demo-company",
            help="Tenant slug to reset (default: demo-company).",
        )

    def handle(self, *args, **options):
        tenant = Tenant.objects.filter(slug=options["tenant_slug"]).first()
        if not tenant:
            self.stderr.write(self.style.ERROR(f"Tenant not found: {options['tenant_slug']}"))
            return

        if not options["safe"] and not options.get("reseed"):
            self.stdout.write(self.style.WARNING("Use --safe to confirm reset."))
            return

        results = reset_safe_demo_data(tenant, reseed=options["reseed"])
        self.stdout.write(self.style.SUCCESS(f"Reset complete for {tenant.name}"))
        for key, value in results.items():
            self.stdout.write(f"  {key}: {value}")
