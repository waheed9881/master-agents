#!/usr/bin/env python
"""
Seed CRM demo data: pipeline stages, contacts, leads, deals, tasks.

Usage:
    python scripts/seed_crm_demo.py
"""
import os
import sys
from decimal import Decimal

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.crm.models import LeadStatus
from apps.crm.services import (
    create_contact,
    create_follow_up_task,
    create_lead,
    create_task,
    ensure_default_pipeline_stages,
    update_lead_score,
)
from apps.tenants.models import Tenant

SAMPLE_LEADS = [
    {
        "contact": {
            "name": "Ahmed Hassan",
            "email": "ahmed@techstartup.pk",
            "phone": "+92-300-1234567",
            "city": "Karachi",
            "country": "PK",
            "source": "web_chat",
        },
        "lead": {
            "title": "WhatsApp automation for e-commerce store",
            "status": LeadStatus.HOT,
            "budget": "$500-1000/month",
            "need": "Automate customer support and sales on WhatsApp",
            "timeline": "Within 2 weeks",
            "summary": "Hot lead — wants demo this week, budget confirmed.",
        },
        "deal_value": Decimal("9000"),
        "stage_name": "Qualified",
    },
    {
        "contact": {
            "name": "Sarah Johnson",
            "email": "sarah@retailco.com",
            "phone": "+1-555-0142",
            "city": "New York",
            "country": "USA",
            "source": "instagram",
        },
        "lead": {
            "title": "Instagram DM sales agent for fashion brand",
            "status": LeadStatus.QUALIFYING,
            "budget": "$300-500/month",
            "need": "Handle Instagram DMs and qualify leads",
            "timeline": "1 month",
            "summary": "Interested in Instagram integration, still comparing options.",
        },
        "deal_value": Decimal("4800"),
        "stage_name": "Qualifying",
    },
    {
        "contact": {
            "name": "Khalid Al-Rashid",
            "email": "khalid@proptech.ae",
            "phone": "+971-50-9876543",
            "city": "Dubai",
            "country": "UAE",
            "source": "web_chat",
        },
        "lead": {
            "title": "Sales agent for real estate listings",
            "status": LeadStatus.QUALIFIED,
            "budget": "$1000+/month",
            "need": "Qualify property buyers via WhatsApp",
            "timeline": "Within 30 days",
            "summary": "Qualified buyer, ready for proposal.",
        },
        "deal_value": Decimal("12000"),
        "stage_name": "Proposal",
    },
    {
        "contact": {
            "name": "Fatima Khan",
            "email": "fatima@clinic.sa",
            "phone": "+966-55-1234567",
            "city": "Riyadh",
            "country": "KSA",
            "source": "referral",
        },
        "lead": {
            "title": "Patient follow-up automation inquiry",
            "status": LeadStatus.NEW,
            "budget": "",
            "need": "Appointment reminders and follow-ups",
            "timeline": "Exploring options",
            "summary": "Early stage inquiry, needs more qualification.",
        },
        "deal_value": Decimal("0"),
        "stage_name": "New",
    },
    {
        "contact": {
            "name": "Mike Chen",
            "email": "mike@saas.io",
            "phone": "+1-555-0199",
            "city": "San Francisco",
            "country": "USA",
            "source": "web_chat",
        },
        "lead": {
            "title": "Demo booked — SaaS sales automation",
            "status": LeadStatus.DEMO_BOOKED,
            "budget": "$2000/month",
            "need": "Full sales closing agent for B2B SaaS",
            "timeline": "Immediate",
            "summary": "Demo scheduled for Thursday 2pm EST.",
        },
        "deal_value": Decimal("24000"),
        "stage_name": "Negotiation",
    },
]


def seed_crm_for_tenant(tenant: Tenant, agent_instance=None):
    """Seed CRM data for a tenant."""
    stages = ensure_default_pipeline_stages(tenant)
    stage_map = {s.name: s for s in stages}

    if tenant.leads.exists():
        print(f"  CRM data already exists for {tenant.name}, skipping.")
        return

    for sample in SAMPLE_LEADS:
        contact = create_contact(tenant, **sample["contact"])
        lead = create_lead(
            tenant,
            contact,
            agent_instance=agent_instance,
            **sample["lead"],
        )
        update_lead_score(lead)

        stage = stage_map.get(sample["stage_name"], stages[0])
        deal = lead.deals.first()
        if deal:
            deal.stage = stage
            deal.value = sample["deal_value"]
            deal.currency = tenant.default_currency
            deal.probability = min(lead.score, 95)
            deal.save()

        if lead.status in (LeadStatus.HOT, LeadStatus.DEMO_BOOKED):
            create_follow_up_task(lead, days_ahead=1)
        elif lead.status == LeadStatus.QUALIFYING:
            create_task(
                tenant,
                lead=lead,
                title=f"Send pricing info to {contact.name}",
                description="Lead is comparing options — send comparison sheet.",
            )

    print(f"  Seeded {len(SAMPLE_LEADS)} leads for {tenant.name}")


def seed():
    tenant = Tenant.objects.filter(slug="demo-company").first()
    if not tenant:
        print("Demo tenant not found. Run seed_demo_data.py first.")
        return

    agent_instance = tenant.agent_instances.first()
    seed_crm_for_tenant(tenant, agent_instance=agent_instance)
    print("CRM demo data seeded successfully.")


if __name__ == "__main__":
    seed()
