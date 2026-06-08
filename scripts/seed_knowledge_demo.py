#!/usr/bin/env python
"""
Seed sample knowledge base entries for the demo tenant.

Usage:
    python scripts/seed_knowledge_demo.py
"""
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.knowledge.models import KnowledgeSourceType
from apps.knowledge.services import create_knowledge_source
from apps.tenants.models import Tenant

SAMPLE_SOURCES = [
    {
        "title": "Product Overview",
        "source_type": KnowledgeSourceType.TEXT,
        "content": (
            "AI Agent OS helps businesses deploy AI sales agents on WhatsApp, Instagram, "
            "and web chat. Agents qualify leads, answer from your knowledge base, update CRM, "
            "and hand off to humans when needed. Setup takes minutes with pre-built templates."
        ),
    },
    {
        "title": "Pricing Plans",
        "source_type": KnowledgeSourceType.PRICING,
        "content": (
            "Starter plan: $299 per month. Includes 1 active agent and web chat widget.\n\n"
            "Growth plan: $599 per month. Includes 3 agents with WhatsApp and Instagram channels.\n\n"
            "Enterprise plan: Custom pricing. Unlimited agents, priority support, and SLA options.\n\n"
            "All plans include CRM integration, inbox, and knowledge base. Annual billing saves 15 percent."
        ),
    },
    {
        "title": "FAQ - Getting Started",
        "source_type": KnowledgeSourceType.FAQ,
        "content": (
            "Q: How long does setup take?\n"
            "A: Most businesses go live in under one hour after adding knowledge and deploying an agent.\n\n"
            "Q: Do I need a developer?\n"
            "A: No. The dashboard lets you configure agents, knowledge, and channels without code.\n\n"
            "Q: Can the agent book demos?\n"
            "A: Yes. The sales agent qualifies leads and can schedule demo calls when customers ask."
        ),
    },
    {
        "title": "Refund and Cancellation Policy",
        "source_type": KnowledgeSourceType.POLICY,
        "content": (
            "Monthly plans can be cancelled anytime with 30 days notice. Refunds are prorated for "
            "unused days within the current billing period. Enterprise contracts follow signed terms. "
            "Contact support@example.com for billing questions."
        ),
    },
    {
        "title": "WhatsApp Integration Requirements",
        "source_type": KnowledgeSourceType.TEXT,
        "content": (
            "WhatsApp Business API requires a verified Meta Business account and approved phone number. "
            "Growth and Enterprise plans include WhatsApp channel setup assistance. Message templates "
            "must be approved by Meta before outbound campaigns."
        ),
    },
]


def seed_knowledge_for_tenant(tenant: Tenant, agent_instance=None):
    """Seed knowledge sources for a tenant (idempotent)."""
    existing_titles = set(
        tenant.knowledge_sources.filter(title__in=[s["title"] for s in SAMPLE_SOURCES])
        .values_list("title", flat=True)
    )
    if len(existing_titles) == len(SAMPLE_SOURCES):
        print(f"  Knowledge data already exists for {tenant.name}, skipping.")
        return

    created = 0
    for sample in SAMPLE_SOURCES:
        if sample["title"] in existing_titles:
            continue
        create_knowledge_source(
            tenant,
            title=sample["title"],
            content=sample["content"],
            source_type=sample["source_type"],
            agent_instance=agent_instance,
        )
        created += 1

    print(f"  Seeded {created} knowledge sources for {tenant.name}")


def seed():
    tenant = Tenant.objects.filter(slug="demo-company").first()
    if not tenant:
        print("Demo tenant not found. Run seed_demo_data.py first.")
        return

    agent_instance = tenant.agent_instances.first()
    seed_knowledge_for_tenant(tenant, agent_instance=agent_instance)
    print("Knowledge demo data seeded successfully.")


if __name__ == "__main__":
    seed()
