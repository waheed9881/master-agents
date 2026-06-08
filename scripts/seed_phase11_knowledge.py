#!/usr/bin/env python
"""Seed per-agent knowledge sources for Phase 11 demo."""
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.agents.models import AgentInstance
from apps.knowledge.models import KnowledgeSourceType
from apps.knowledge.services import create_knowledge_source
from apps.tenants.models import Tenant

AGENT_KNOWLEDGE = {
    "sales-closing-agent": [
        ("Sales Process Overview", KnowledgeSourceType.TEXT, "Qualify leads by service, budget, and timeline. Book demos when requested. Hot leads get priority follow-up."),
        ("Pricing Disclaimer", KnowledgeSourceType.POLICY, "Pricing is indicative only. Final quotes and contracts are confirmed by human sales staff, not the AI assistant."),
    ],
    "real-estate-agent": [
        ("Property Buying Process", KnowledgeSourceType.TEXT, "Buyers submit budget and location. We match listings and schedule viewings within 48 hours."),
        ("Visit Booking Policy", KnowledgeSourceType.POLICY, "Viewings are confirmed by staff. Same-day visits may be available for hot leads."),
        ("Commission Disclaimer", KnowledgeSourceType.POLICY, "Final pricing and commission are confirmed by licensed agents, not the AI assistant."),
    ],
    "clinic-agent": [
        ("Appointment Policy", KnowledgeSourceType.POLICY, "Appointments require name, phone, and preferred time. Confirmation sent by SMS."),
        ("Services Offered", KnowledgeSourceType.TEXT, "General practice, dental, pediatrics, and lab services available Mon-Sat."),
        ("Urgent Care Disclaimer", KnowledgeSourceType.POLICY, "For emergencies call emergency services. AI cannot diagnose or prescribe medication."),
    ],
    "home-services-agent": [
        ("Service Categories", KnowledgeSourceType.TEXT, "Plumbing, electrical, HVAC, painting, and renovation services."),
        ("Quote Process", KnowledgeSourceType.POLICY, "Estimates provided after site visit or photo review. Final quote approved by estimator."),
        ("Emergency Handling", KnowledgeSourceType.POLICY, "Gas leaks and electrical hazards are escalated immediately to on-call technicians."),
    ],
    "school-agent": [
        ("Admissions FAQ", KnowledgeSourceType.FAQ, "Admissions open Jan-Mar. Required: birth certificate, previous report card, parent ID."),
        ("Fees and Timetable", KnowledgeSourceType.PRICING, "Tuition varies by grade. School hours 8am-2pm. After-school programs until 5pm."),
    ],
    "voice-agent": [
        ("Business Hours", KnowledgeSourceType.TEXT, "Monday-Friday 9am-6pm. Saturday 10am-2pm. Closed Sundays."),
        ("Callback Process", KnowledgeSourceType.POLICY, "Callbacks scheduled within 2 business hours during office hours."),
    ],
    "tender-agent": [
        ("Proposal Workflow", KnowledgeSourceType.TEXT, "Submit RFP → requirements review → draft proposal → compliance check → human approval."),
        ("Required Documents Checklist", KnowledgeSourceType.POLICY, "Company profile, financial statements, technical proposal, compliance certificates."),
    ],
    "ecommerce-agent": [
        ("Order and Refund Policy", KnowledgeSourceType.POLICY, "Orders ship in 2-3 days. Refunds within 14 days for unused items. Exchanges within 30 days."),
        ("Product Support FAQ", KnowledgeSourceType.FAQ, "For order tracking provide order ID. Refund approval is handled by support staff, not guaranteed by AI."),
    ],
    "recruitment-agent": [
        ("Hiring Process", KnowledgeSourceType.TEXT, "Apply → AI screening → HR review → interview → offer."),
        ("Screening Questions", KnowledgeSourceType.FAQ, "We ask about role fit, experience, salary expectations, and availability."),
    ],
    "finance-agent": [
        ("Invoice Payment Process", KnowledgeSourceType.TEXT, "Invoices due in 30 days. Payment via bank transfer or card. Reminders sent at 7 days before due."),
        ("Financial Disclaimer", KnowledgeSourceType.POLICY, "AI assistant is not a licensed accountant. Tax and legal advice requires professional staff."),
    ],
}

AGENT_SETTINGS = {
    "sales-closing-agent": {
        "business_name": "Demo Company",
        "services_json": ["WhatsApp Sales", "Instagram DM", "Web Chat", "CRM"],
    },
    "real-estate-agent": {
        "business_name": "Demo Realty",
        "services_json": ["Residential sales", "Rentals", "Property tours"],
    },
    "clinic-agent": {
        "business_name": "Demo Health Clinic",
        "services_json": ["General practice", "Dental", "Pediatrics"],
    },
    "home-services-agent": {
        "business_name": "Demo Home Services",
        "services_json": ["Plumbing", "Electrical", "Renovation"],
    },
    "school-agent": {
        "business_name": "Demo Academy",
        "services_json": ["Admissions", "Fee inquiries", "Campus tours"],
    },
    "voice-agent": {
        "business_name": "Demo Business Reception",
        "services_json": ["Call answering", "Appointments", "Callbacks"],
    },
    "tender-agent": {
        "business_name": "Demo Proposals Co",
        "services_json": ["RFP response", "Proposal drafting", "Compliance review"],
    },
    "ecommerce-agent": {
        "business_name": "Demo Store",
        "services_json": ["Order tracking", "Returns", "Product support"],
    },
    "recruitment-agent": {
        "business_name": "Demo HR",
        "services_json": ["Candidate screening", "Interview scheduling"],
    },
    "finance-agent": {
        "business_name": "Demo Finance Desk",
        "services_json": ["Invoices", "Payments", "Bookkeeping support"],
    },
}


def seed_phase11_for_tenant(tenant: Tenant):
    from apps.agents.services import update_agent_settings

    for slug, sources in AGENT_KNOWLEDGE.items():
        instance = AgentInstance.objects.filter(tenant=tenant, template__slug=slug).first()
        if not instance:
            continue
        settings = AGENT_SETTINGS.get(slug, {})
        if settings:
            update_agent_settings(instance, **settings)
        existing = set(
            instance.knowledge_sources.values_list("title", flat=True)
        )
        for title, source_type, content in sources:
            if title in existing:
                continue
            create_knowledge_source(
                tenant,
                title=title,
                content=content,
                source_type=source_type,
                agent_instance=instance,
            )


if __name__ == "__main__":
    tenant = Tenant.objects.filter(slug="demo-company").first()
    if tenant:
        seed_phase11_for_tenant(tenant)
        print("Phase 11 knowledge seeded.")
