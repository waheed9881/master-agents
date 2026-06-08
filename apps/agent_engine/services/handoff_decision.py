"""Decide when to hand off conversation to a human."""
from dataclasses import dataclass


@dataclass
class HandoffDecision:
    should_handoff: bool
    reason: str = ""


class HandoffDecisionService:
    """Evaluate handoff triggers from message, intent, and confidence."""

    HANDOFF_INTENTS = {
        "complaint",
        "handoff_request",
        "ready_to_buy",
        "discount_request",
        "sensitive_topic",
        "custom_quote",
    }

    ANGRY_WORDS = ("angry", "terrible", "worst", "refund", "sue", "lawyer", "scam")
    SENSITIVE_WORDS = ("legal guarantee", "medical", "financial advice", "guarantee results")
    CONFIDENCE_THRESHOLD = 0.6

    @classmethod
    def evaluate(
        cls,
        message: str,
        *,
        intent: str = "",
        confidence: float = 1.0,
        extracted_signals: list[str] | None = None,
    ) -> HandoffDecision:
        lower = message.lower()
        signals = extracted_signals or []

        if intent in cls.HANDOFF_INTENTS:
            return HandoffDecision(True, f"intent:{intent}")

        if any(w in lower for w in cls.ANGRY_WORDS):
            return HandoffDecision(True, "angry_customer")

        if any(w in lower for w in cls.SENSITIVE_WORDS):
            return HandoffDecision(True, "sensitive_topic")

        if any(w in lower for w in ("custom quote", "custom pricing", "enterprise quote")):
            return HandoffDecision(True, "custom_quote_request")

        if any(w in lower for w in ("ready to pay", "buy now", "purchase today")):
            return HandoffDecision(True, "ready_to_pay")

        if "speak with human" in signals or "handoff" in signals:
            return HandoffDecision(True, "explicit_handoff")

        if confidence < cls.CONFIDENCE_THRESHOLD:
            return HandoffDecision(True, "low_ai_confidence")

        return HandoffDecision(False)
