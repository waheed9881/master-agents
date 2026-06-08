#!/usr/bin/env python
"""
Seed demo tenant and owner user for local development.

Usage:
    python manage.py shell < scripts/seed_demo_data.py
    # or
    python scripts/seed_demo_data.py
"""
import os
import sys

import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.accounts.models import User, UserRole
from apps.agents.models import AgentTemplate
from apps.agents.services import create_agent_instance
from apps.tenants.models import Tenant
from apps.tenants.services import create_tenant


def seed():
    tenant, created = Tenant.objects.get_or_create(
        slug="demo-company",
        defaults={
            "name": "Demo Company",
            "country": "USA",
            "industry": "Technology",
            "timezone": "America/New_York",
            "default_currency": "USD",
        },
    )
    action = "Created" if created else "Updated"
    print(f"{action} tenant: {tenant.name}")

    user, created = User.objects.get_or_create(
        email="admin@example.com",
        defaults={
            "full_name": "Demo Admin",
            "role": UserRole.OWNER,
            "tenant": tenant,
            "is_staff": True,
            "is_superuser": True,
        },
    )
    if created:
        user.set_password("Admin123!")
        user.save()
        print(f"Created user: {user.email} (password: Admin123!)")
    else:
        user.tenant = tenant
        user.set_password("Admin123!")
        user.save()
        print(f"Reset password for: {user.email} (password: Admin123!)")

    # Seed agent templates if not present
    if AgentTemplate.objects.count() == 0:
        print("\nSeeding agent templates...")
        import importlib.util
        from pathlib import Path

        tpl_path = Path(__file__).parent / "seed_agent_templates.py"
        spec = importlib.util.spec_from_file_location("seed_agent_templates", tpl_path)
        tpl_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tpl_mod)
        tpl_mod.seed()

    # Deploy Sales Closing Agent for demo tenant
    from apps.agents.models import AgentInstanceStatus

    sales_template = AgentTemplate.objects.filter(slug="sales-closing-agent").first()
    if sales_template and not tenant.agent_instances.filter(template=sales_template).exists():
        instance = create_agent_instance(
            tenant=tenant,
            template=sales_template,
            status=AgentInstanceStatus.ACTIVE,
        )
        print(f"\nDeployed demo agent: {instance.name}")

        from apps.agents.services import update_agent_settings

        update_agent_settings(
            instance,
            business_name="Demo Company",
            business_description="AI Agent OS helps businesses deploy sales agents on WhatsApp, Instagram, and web chat.",
            services_json=[
                "WhatsApp Sales Agent",
                "Instagram DM Automation",
                "Web Chat Widget",
                "CRM Integration",
            ],
            pricing_json={
                "Starter": "$299/month — 1 agent, web chat",
                "Growth": "$599/month — 3 agents, WhatsApp + Instagram",
                "Enterprise": "Custom pricing — unlimited agents + priority support",
            },
        )

    # Seed CRM demo data
    import importlib.util
    from pathlib import Path

    crm_path = Path(__file__).parent / "seed_crm_demo.py"
    spec = importlib.util.spec_from_file_location("seed_crm_demo", crm_path)
    seed_crm_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seed_crm_mod)
    seed_crm_mod.seed_crm_for_tenant(tenant, agent_instance=tenant.agent_instances.first())

    # Seed inbox demo conversations
    crm_path = Path(__file__).parent / "seed_inbox_demo.py"
    spec = importlib.util.spec_from_file_location("seed_inbox_demo", crm_path)
    seed_inbox_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seed_inbox_mod)
    seed_inbox_mod.seed_inbox_for_tenant(tenant, agent_instance=tenant.agent_instances.first())

    print("\nDemo login:")
    print("  Email: admin@example.com")
    print("  Password: Admin123!")
    print("\nWARNING: Change the demo password before deploying to production!")


if __name__ == "__main__":
    seed()
