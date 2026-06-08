#!/usr/bin/env python
"""
Seed demo channel accounts for web chat, WhatsApp, and Instagram.

Usage:
    python scripts/seed_integrations_demo.py
"""
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.inbox.models import ChannelAccount, ChannelType
from apps.integrations.models import ChannelCredential
from apps.tenants.models import Tenant

DEMO_PHONE_NUMBER_ID = "demo_phone_number_id"
DEMO_INSTAGRAM_PAGE_ID = "demo_instagram_page_id"

CHANNELS = [
    {
        "channel_type": ChannelType.WEB_CHAT,
        "display_name": "Web Chat Demo",
        "phone_number_id": "",
        "page_id": "",
    },
    {
        "channel_type": ChannelType.WHATSAPP,
        "display_name": "WhatsApp Demo Channel",
        "phone_number_id": DEMO_PHONE_NUMBER_ID,
        "page_id": "",
    },
    {
        "channel_type": ChannelType.INSTAGRAM,
        "display_name": "Instagram Demo Channel",
        "phone_number_id": "",
        "page_id": DEMO_INSTAGRAM_PAGE_ID,
    },
]


def seed_integrations_for_tenant(tenant: Tenant):
    """Create demo channel accounts and credentials (idempotent)."""
    created = 0
    for item in CHANNELS:
        account, account_created = ChannelAccount.objects.get_or_create(
            tenant=tenant,
            channel_type=item["channel_type"],
            display_name=item["display_name"],
            defaults={"is_active": True},
        )
        if account_created:
            created += 1

        cred, cred_created = ChannelCredential.objects.get_or_create(
            tenant=tenant,
            channel_account=account,
            defaults={
                "provider": "meta",
                "phone_number_id": item["phone_number_id"],
                "page_id": item["page_id"],
                "verify_token": "ai-agent-os-verify",
                "is_active": True,
            },
        )
        if not cred_created:
            updated = False
            if item["phone_number_id"] and cred.phone_number_id != item["phone_number_id"]:
                cred.phone_number_id = item["phone_number_id"]
                updated = True
            if item["page_id"] and cred.page_id != item["page_id"]:
                cred.page_id = item["page_id"]
                updated = True
            if updated:
                cred.save()

    if created:
        print(f"  Seeded {created} channel accounts for {tenant.name}")
    else:
        print(f"  Integration channels already exist for {tenant.name}, skipping.")


def seed():
    tenant = Tenant.objects.filter(slug="demo-company").first()
    if not tenant:
        print("Demo tenant not found. Run seed_demo_data.py first.")
        return
    seed_integrations_for_tenant(tenant)
    print("Integrations demo data seeded successfully.")


if __name__ == "__main__":
    seed()
