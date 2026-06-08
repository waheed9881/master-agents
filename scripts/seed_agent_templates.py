#!/usr/bin/env python
"""
Seed all 10 AI agent templates.

Usage:
    python scripts/seed_agent_templates.py
"""
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.agents.models import AgentTemplate

AGENT_TEMPLATES = [
    {
        "name": "WhatsApp + Instagram Sales Closing Agent",
        "slug": "sales-closing-agent",
        "description": (
            "Qualify leads, answer product questions, handle objections, and book demos "
            "across WhatsApp, Instagram DMs, and web chat. Automatically scores leads, "
            "detects hot prospects, and hands off to humans when needed."
        ),
        "category": "Sales & Revenue",
        "priority_label": "Build first",
        "market_need_score": 97,
        "tags_json": ["PK", "KSA", "USA", "UAE", "High demand", "Priority 1", "Sales"],
        "default_workflow_json": {
            "steps": [
                "Greet customer and identify intent",
                "Ask qualification questions (service, business type, budget, timeline)",
                "Search knowledge base for accurate answers",
                "Handle objections using configured responses",
                "Score lead and detect hot prospects",
                "Book demo/call or hand off to human sales rep",
            ]
        },
        "default_prompt": (
            "You are a professional sales assistant for {business_name}. "
            "Qualify leads, answer from knowledge base only, never invent pricing, "
            "and hand off sensitive decisions to humans."
        ),
        "is_implemented": True,
    },
    {
        "name": "Real Estate AI Sales Agent",
        "slug": "real-estate-agent",
        "description": (
            "Handle property inquiries, schedule viewings, qualify buyers by budget "
            "and location, and follow up on leads automatically."
        ),
        "category": "Real Estate",
        "priority_label": "High demand",
        "market_need_score": 88,
        "tags_json": ["PK", "KSA", "UAE", "Real Estate", "Growing"],
        "default_workflow_json": {
            "steps": [
                "Identify property interest (buy/rent/invest)",
                "Collect budget, location, and timeline",
                "Match properties from inventory",
                "Schedule viewing or virtual tour",
                "Follow up and nurture lead",
            ]
        },
        "default_prompt": (
            "You are a real estate sales assistant for {business_name}. "
            "Qualify buyers by property type, location, budget, and timeline. "
            "Schedule viewings but hand off final pricing and legal paperwork to staff."
        ),
        "is_implemented": True,
    },
    {
        "name": "Clinic Receptionist + Patient Follow-up Agent",
        "slug": "clinic-agent",
        "description": (
            "Book appointments, answer common health service questions, send reminders, "
            "and follow up with patients post-visit. Never gives medical advice."
        ),
        "category": "Healthcare",
        "priority_label": "High demand",
        "market_need_score": 85,
        "tags_json": ["PK", "KSA", "USA", "Healthcare", "Growing"],
        "default_workflow_json": {
            "steps": [
                "Greet patient and identify need",
                "Check appointment availability",
                "Book or reschedule appointment",
                "Send confirmation and reminders",
                "Post-visit follow-up",
            ]
        },
        "default_prompt": (
            "You are a clinic receptionist for {business_name}. "
            "Book appointments, answer service questions from knowledge only. "
            "Never diagnose or prescribe. Escalate urgent symptoms to staff immediately."
        ),
        "is_implemented": True,
    },
    {
        "name": "Home Services / Contractor Bidding Agent",
        "slug": "home-services-agent",
        "description": (
            "Collect project details, provide estimate ranges, schedule site visits, "
            "and qualify homeowners for renovation and repair services."
        ),
        "category": "Home Services",
        "priority_label": "Growing",
        "market_need_score": 78,
        "tags_json": ["USA", "UAE", "Contractor", "Growing"],
        "default_workflow_json": {
            "steps": [
                "Identify service type (plumbing, electrical, renovation)",
                "Collect project scope and photos",
                "Provide estimate range from pricing config",
                "Schedule site visit",
                "Generate follow-up task for estimator",
            ]
        },
        "default_prompt": (
            "You are a home services assistant for {business_name}. "
            "Collect service details, location, urgency, and photos. Hand off final quotes to estimators."
        ),
        "is_implemented": True,
    },
    {
        "name": "School / Academy Admin Agent",
        "slug": "school-agent",
        "description": (
            "Handle admissions inquiries, share program details, schedule campus tours, "
            "and manage parent communication for schools and academies."
        ),
        "category": "Education",
        "priority_label": "Growing",
        "market_need_score": 72,
        "tags_json": ["PK", "KSA", "UAE", "Education"],
        "default_workflow_json": {
            "steps": [
                "Identify program interest",
                "Share curriculum and fee structure",
                "Collect student details",
                "Schedule campus tour or info session",
                "Follow up on application status",
            ]
        },
        "default_prompt": (
            "You are a school admissions assistant for {business_name}. "
            "Answer from knowledge about programs, fees, and timetables. Hand off complaints to staff."
        ),
        "is_implemented": True,
    },
    {
        "name": "AI Voice Receptionist for SMEs",
        "slug": "voice-agent",
        "description": (
            "Answer phone calls, route to departments, take messages, and handle "
            "common business inquiries with natural voice interaction."
        ),
        "category": "Voice & Telephony",
        "priority_label": "High demand",
        "market_need_score": 82,
        "tags_json": ["USA", "KSA", "Global", "Voice"],
        "default_workflow_json": {
            "steps": [
                "Answer call with business greeting",
                "Identify caller intent",
                "Route to department or take message",
                "Answer FAQs from knowledge base",
                "Log call summary to CRM",
            ]
        },
        "default_prompt": (
            "You are a text-mode receptionist for {business_name}. "
            "Give short professional replies. Collect caller details and arrange callbacks."
        ),
        "is_implemented": True,
    },
    {
        "name": "AI Tender / Proposal Writing Agent",
        "slug": "tender-agent",
        "description": (
            "Assist with RFP responses, generate proposal drafts from templates, "
            "and track submission deadlines for government and corporate tenders."
        ),
        "category": "B2B / Government",
        "priority_label": "Growing",
        "market_need_score": 70,
        "tags_json": ["PK", "KSA", "UAE", "B2B"],
        "default_workflow_json": {
            "steps": [
                "Parse tender requirements",
                "Match company capabilities",
                "Draft proposal sections",
                "Review compliance checklist",
                "Hand off for human review and submission",
            ]
        },
        "default_prompt": (
            "You are a tender/proposal assistant for {business_name}. "
            "Collect RFP details, deadlines, and documents. Hand off final proposals to staff."
        ),
        "is_implemented": True,
    },
    {
        "name": "eCommerce Support + Order Tracking Agent",
        "slug": "ecommerce-agent",
        "description": (
            "Handle order status inquiries, returns, product questions, and upsell "
            "recommendations for online stores."
        ),
        "category": "eCommerce",
        "priority_label": "High demand",
        "market_need_score": 90,
        "tags_json": ["Global", "USA", "UAE", "eCommerce"],
        "default_workflow_json": {
            "steps": [
                "Identify order or product inquiry",
                "Look up order status",
                "Answer product questions from catalog",
                "Process return/refund request (hand off)",
                "Suggest related products",
            ]
        },
        "default_prompt": (
            "You are an eCommerce support assistant for {business_name}. "
            "Help with orders, products, and returns per policy. Do not guarantee refunds without policy support."
        ),
        "is_implemented": True,
    },
    {
        "name": "AI Recruitment Screening Agent",
        "slug": "recruitment-agent",
        "description": (
            "Screen candidates, ask role-specific questions, score fit, and schedule "
            "interviews with hiring managers."
        ),
        "category": "HR & Recruitment",
        "priority_label": "Growing",
        "market_need_score": 75,
        "tags_json": ["Global", "USA", "PK", "HR"],
        "default_workflow_json": {
            "steps": [
                "Collect candidate basic info",
                "Ask role-specific screening questions",
                "Score candidate fit",
                "Schedule interview with hiring manager",
                "Send rejection or advance notification",
            ]
        },
        "default_prompt": (
            "You are a recruitment screening assistant for {business_name}. "
            "Ask role-specific screening questions. Hand off interviews and offers to HR."
        ),
        "is_implemented": True,
    },
    {
        "name": "AI Finance / Bookkeeping Assistant",
        "slug": "finance-agent",
        "description": (
            "Answer common accounting questions, categorize expenses, generate invoice "
            "reminders, and hand off tax/legal questions to professionals."
        ),
        "category": "Finance",
        "priority_label": "Growing",
        "market_need_score": 68,
        "tags_json": ["USA", "UAE", "Global", "Finance"],
        "default_workflow_json": {
            "steps": [
                "Identify finance inquiry type",
                "Answer from knowledge base (no tax advice)",
                "Categorize transaction or expense",
                "Generate invoice reminder",
                "Hand off complex queries to accountant",
            ]
        },
        "default_prompt": (
            "You are a finance assistant for {business_name} (not a licensed advisor). "
            "Collect invoice and payment details. Hand off tax and legal questions to professionals."
        ),
        "is_implemented": True,
    },
]


def seed():
    created_count = 0
    updated_count = 0
    for data in AGENT_TEMPLATES:
        _, created = AgentTemplate.objects.update_or_create(
            slug=data["slug"],
            defaults=data,
        )
        if created:
            created_count += 1
            print(f"  Created: {data['name']}")
        else:
            updated_count += 1
            print(f"  Updated: {data['name']}")

    print(f"\nDone: {created_count} created, {updated_count} updated.")
    print(f"Total templates: {AgentTemplate.objects.count()}")


if __name__ == "__main__":
    print("Seeding agent templates...")
    seed()
