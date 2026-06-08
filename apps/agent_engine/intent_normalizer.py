"""Central intent normalization — aliases to canonical intent labels."""

from __future__ import annotations

# Global aliases applied across all domains.
GLOBAL_INTENT_ALIASES: dict[str, str] = {
    "price_question": "pricing_inquiry",
    "pricing": "pricing_inquiry",
    "price_inquiry": "pricing_inquiry",
    "appointment": "appointment_request",
    "quote": "quote_request",
    "final_quote": "quote_request",
    "refund": "refund_request",
    "visit": "visit_request",
    "visit_booking": "visit_request",
    "human": "handoff_request",
    "human_request": "handoff_request",
    "human_handoff": "handoff_request",
    "job_apply": "job_application",
    "angry_customer": "complaint",
    "handoff": "handoff_request",
    "demo": "demo_request",
    "sensitive": "sensitive_topic",
    "general_inquiry": "general",
    "inquiry": "general",
    "call_back": "callback_request",
    "hours_inquiry": "business_hours",
    "rfp": "rfp_upload",
    "proposal": "proposal_request",
    "order_tracking": "order_status",
    "product_inquiry": "product_question",
    "cv": "cv_submission",
    "resume": "cv_submission",
    "interview": "interview_request",
    "salary": "salary_expectation",
    "tax": "tax_question",
    "tax_advice": "tax_question",
    "bookkeeping": "bookkeeping_request",
    "expense": "expense_question",
    "fee": "fee_inquiry",
    "tuition": "fee_inquiry",
    "timetable": "timetable_inquiry",
    "schedule": "timetable_inquiry",
    "parent_issue": "parent_complaint",
    "urgent": "urgent_repair",
    "emergency": "urgent_repair",
    "property": "property_inquiry",
    "investment": "investment_inquiry",
    "symptoms": "symptoms_shared",
    "lab_report": "report_followup",
    "exchange": "exchange_request",
    "payment": "payment_reminder",
    "invoice": "invoice_question",
    "requirements": "requirement_extraction",
    "deadline": "deadline_shared",
    "pricing_scope_inquiry": "pricing_scope",
    "ready_to_purchase": "ready_to_buy",
    "discount": "discount_request",
    "contact": "contact_shared",
    "budget": "budget_shared",
    "timeline": "timeline_shared",
    "greeting_hello": "greeting",
    "reception": "call_answering",
    "phone_call": "call_answering",
    "meeting": "meeting_request",
    "availability": "availability_shared",
}

# Per-domain aliases (merged with global at lookup time).
DOMAIN_INTENT_ALIASES: dict[str, dict[str, str]] = {
    "sales": {
        "pricing_question": "pricing_inquiry",
        "buy_now": "ready_to_buy",
    },
    "real_estate": {
        "viewing": "visit_request",
        "viewing_request": "visit_request",
        "location": "location_shared",
        "roi_inquiry": "investment_inquiry",
    },
    "clinic": {
        "appointment": "appointment_request",
        "appointment_booking": "appointment_request",
        "medical_emergency": "sensitive_topic",
        "prescription": "sensitive_topic",
    },
    "home_services": {
        "emergency_repair": "urgent_repair",
        "estimate": "quote_request",
    },
    "school": {
        "admission": "admission_inquiry",
        "fees": "fee_inquiry",
        "schedule_question": "timetable_inquiry",
    },
    "voice": {
        "urgent_callback": "callback_request",
        "phone_greeting": "call_answering",
        "opening_hours": "business_hours",
        "appointment_request": "appointment_booking",
        "demo_request": "appointment_booking",
    },
    "tender": {
        "rfp_submission": "rfp_upload",
        "compliance": "sensitive_topic",
        "final_pricing": "pricing_scope",
    },
    "ecommerce": {
        "return": "refund_request",
        "damaged_product": "complaint",
    },
    "recruitment": {
        "apply": "job_application",
        "offer_negotiation": "salary_expectation",
    },
    "finance": {
        "billing": "invoice_question",
        "accounts": "bookkeeping_request",
    },
}


def normalize_intent(intent: str, domain: str | None = None) -> str:
    """Map an intent label to its canonical form."""
    if not intent:
        return "general"
    key = intent.strip().lower().replace(" ", "_").replace("-", "_")
    if domain:
        domain_key = domain.strip().lower().replace(" ", "_").replace("-", "_")
        domain_aliases = DOMAIN_INTENT_ALIASES.get(domain_key, {})
        if key in domain_aliases:
            return domain_aliases[key]
    if key in GLOBAL_INTENT_ALIASES:
        return GLOBAL_INTENT_ALIASES[key]
    return key


def normalize_intent_set(intents: tuple[str, ...] | list[str], domain: str | None = None) -> frozenset[str]:
    """Normalize a collection of intent labels."""
    return frozenset(normalize_intent(i, domain) for i in intents if i)


def intents_equivalent(
    expected: str,
    actual: str,
    *,
    domain: str | None = None,
    acceptable: tuple[str, ...] | list[str] = (),
) -> tuple[bool, str]:
    """
    Return (matches, reason).
    reason is empty on direct match, otherwise describes alias resolution.
    """
    norm_expected = normalize_intent(expected, domain)
    norm_actual = normalize_intent(actual, domain)
    if norm_actual == norm_expected:
        if actual != expected:
            return True, f"alias:{actual}->{norm_actual}"
        return True, ""
    acceptable_norm = normalize_intent_set(acceptable, domain)
    if norm_actual in acceptable_norm:
        return True, f"acceptable:{actual}"
    return False, f"expected {norm_expected}, got {norm_actual} (raw: {actual})"
