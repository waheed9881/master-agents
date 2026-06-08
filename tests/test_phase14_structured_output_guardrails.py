"""Phase 14 tests: structured output parsing and safety guardrails."""
import pytest

from apps.agent_engine.services.safety_guardrails import evaluate_guardrails
from apps.agent_engine.structured_output import parse_structured_output


class TestStructuredOutput:
    def test_parses_valid_json(self):
        raw = '{"reply_text": "Hello", "intent": "greeting", "confidence": 0.9}'
        result = parse_structured_output(raw, domain="sales")
        assert result.parse_valid is True
        assert result.reply_text == "Hello"
        assert result.intent == "greeting"

    def test_handles_invalid_json_safely(self):
        result = parse_structured_output(
            "Sorry, I cannot help with that today.",
            domain="sales",
            customer_message="Hello",
        )
        assert result.parse_valid is False
        assert result.reply_text
        assert result.parse_source == "fallback_text"


class TestSafetyGuardrails:
    def test_clinic_urgent_handoff(self):
        result = evaluate_guardrails(
            "I have severe chest pain and cannot breathe",
            "Please seek help immediately.",
            domain="clinic",
            intent="sensitive_topic",
        )
        assert result.handoff_required is True
        assert result.flags

    def test_finance_tax_handoff(self):
        result = evaluate_guardrails(
            "I need tax advice on my corporate return",
            "I'll connect you with a tax professional.",
            domain="finance",
            intent="tax_question",
        )
        assert result.handoff_required is True

    def test_ecommerce_blocks_guaranteed_refund(self):
        result = evaluate_guardrails(
            "Can you guarantee my refund?",
            "Your refund is approved and guaranteed today.",
            domain="ecommerce",
            intent="refund_request",
        )
        assert result.safe is False
        assert result.rewritten_reply
        assert result.handoff_required is True
