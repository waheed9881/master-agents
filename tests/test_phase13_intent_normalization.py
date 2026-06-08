"""Phase 13 tests: intent normalization and domain intent registry."""
import pytest

from apps.agent_engine.domain_intents import (
    DOMAIN_CANONICAL_INTENTS,
    detect_intent_from_message,
    get_domain_for_slug,
    resolve_final_intent,
)
from apps.agent_engine.intent_normalizer import intents_equivalent, normalize_intent


class TestIntentNormalization:
    def test_price_aliases_normalize_to_pricing_inquiry(self):
        for alias in ("price_question", "pricing", "pricing_inquiry"):
            assert normalize_intent(alias, "sales") == "pricing_inquiry"

    def test_appointment_aliases(self):
        assert normalize_intent("appointment", "clinic") == "appointment_request"
        assert normalize_intent("appointment_booking", "voice") == "appointment_booking"
        assert normalize_intent("appointment_request", "voice") == "appointment_booking"

    def test_refund_and_human_aliases(self):
        assert normalize_intent("refund", "ecommerce") == "refund_request"
        assert normalize_intent("human_handoff", "sales") == "handoff_request"

    def test_job_application_aliases(self):
        assert normalize_intent("job_apply", "recruitment") == "job_application"

    def test_intents_equivalent_with_acceptable(self):
        matches, reason = intents_equivalent(
            "pricing_inquiry",
            "budget_shared",
            domain="sales",
            acceptable=("budget_shared",),
        )
        assert matches is True
        assert reason.startswith("acceptable:")


class TestDomainIntentRegistry:
    def test_all_ten_domains_registered(self):
        domains = {
            "sales", "real_estate", "clinic", "home_services", "school",
            "voice", "tender", "ecommerce", "recruitment", "finance",
        }
        assert domains == set(DOMAIN_CANONICAL_INTENTS.keys())

    def test_template_slug_mapping(self):
        assert get_domain_for_slug("clinic-agent") == "clinic"
        assert get_domain_for_slug("finance-agent") == "finance"

    def test_sales_pricing_detection(self):
        intent, conf, source = detect_intent_from_message(
            "sales",
            "How much does your WhatsApp automation cost?",
        )
        assert intent == "pricing_inquiry"
        assert conf >= 0.7
        assert source == "detector"

    def test_clinic_urgent_triggers_sensitive_topic(self):
        intent, _, _ = detect_intent_from_message(
            "clinic",
            "I have severe chest pain and cannot breathe properly. Emergency!",
        )
        assert intent == "sensitive_topic"

    def test_finance_tax_triggers_handoff_intent(self):
        intent, _, _ = detect_intent_from_message(
            "finance",
            "I need tax advice on my corporate tax return filing and deductions.",
        )
        assert intent == "tax_question"

    def test_ecommerce_refund_approval_intent(self):
        intent, _, _ = detect_intent_from_message(
            "ecommerce",
            "Can you guarantee my refund will be approved today?",
        )
        assert intent == "refund_request"

    def test_real_estate_legal_paperwork(self):
        intent, _, _ = detect_intent_from_message(
            "real_estate",
            "I need help with the legal paperwork and final price for this contract.",
        )
        assert intent in ("sensitive_topic", "handoff_request", "pricing_scope")

    def test_tender_final_quote_handoff(self):
        intent, _, _ = detect_intent_from_message(
            "tender",
            "We need final pricing approval and legal compliance sign-off for this tender.",
        )
        assert intent in ("pricing_scope", "sensitive_topic")

    def test_resolve_final_intent_prefers_detector(self):
        canonical, raw = resolve_final_intent(
            "school",
            "What time does school start and end for primary students?",
            "general",
        )
        assert canonical == "timetable_inquiry"
        assert raw in ("general", "timetable_inquiry")
