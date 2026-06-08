#!/usr/bin/env python
"""Seed sample inbox conversations for demo tenant."""
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.inbox.models import ChannelType
from apps.integrations.services.message_pipeline import InboundMessageService
from apps.tenants.models import Tenant


def seed_inbox_for_tenant(tenant: Tenant, agent_instance=None):
    if tenant.conversations.exists():
        print(f"  Inbox data already exists for {tenant.name}, skipping.")
        return

    if not agent_instance:
        agent_instance = tenant.agent_instances.filter(status="active").first()
    if not agent_instance:
        print("  No active agent — skipping inbox seed.")
        return

    samples = [
        ("Sarah Mitchell", "Hi, I am interested in your WhatsApp automation service for our retail store.", "sarah.mitchell@retailco.demo"),
        ("Ali Rahman", "What are your pricing plans for a team of five sales reps?", "ali.rahman@techstartup.demo"),
    ]

    for name, msg, email in samples:
        InboundMessageService.process(
            tenant,
            message_text=msg,
            channel_type=ChannelType.WEB_CHAT,
            customer_name=name,
            customer_email=email,
            agent_instance=agent_instance,
            session_key=f"seed-{email}",
        )

    print(f"  Seeded {len(samples)} inbox conversations for {tenant.name}")


def seed():
    tenant = Tenant.objects.filter(slug="demo-company").first()
    if not tenant:
        print("Demo tenant not found.")
        return
    seed_inbox_for_tenant(tenant)


if __name__ == "__main__":
    seed()
