"""Safety guardrails for customer messages and AI replies."""
from __future__ import annotations

from dataclasses import dataclass, field

from apps.agent_engine.demo_scenarios import UNSAFE_REPLY_PHRASES

DOMAIN_HANDOFF_INTENTS = {
    "clinic": {"sensitive_topic"},
    "finance": {"tax_question", "sensitive_topic"},
    "real_estate": {"sensitive_topic", "ready_to_buy"},
    "ecommerce": {"refund_request", "complaint"},
    "tender": {"pricing_scope", "sensitive_topic"},
}

CUSTOMER_URGENT_PATTERNS = (
    "chest pain", "cannot breathe", "emergency", "gas leak",
    "guarantee my refund", "tax advice", "financial advice",
    "legal paperwork", "final pricing approval",
)

REPLY_UNSAFE_PATTERNS = UNSAFE_REPLY_PHRASES + (
    "i diagnose", "i prescribe", "guaranteed results",
    "refund is approved", "appointment is confirmed",
    "i am human", "i'm human", "not a bot",
)


@dataclass
class GuardrailResult:
    safe: bool = True
    flags: list[str] = field(default_factory=list)
    rewritten_reply: str = ""
    handoff_required: bool = False
    reason: str = ""
    status: str = "safe"


def _check_reply_unsafe(reply: str) -> list[str]:
    lower = reply.lower()
    return [p for p in REPLY_UNSAFE_PATTERNS if p and p in lower]


def _check_customer_risk(message: str, domain: str) -> list[str]:
    lower = message.lower()
    flags = []
    for pattern in CUSTOMER_URGENT_PATTERNS:
        if pattern in lower:
            flags.append(f"customer:{pattern}")
    if domain == "clinic" and any(w in lower for w in ("prescribe", "diagnose", "medicine")):
        flags.append("clinic:no_prescription")
    if domain == "finance" and any(w in lower for w in ("tax advice", "invest", "financial advice")):
        flags.append("finance:no_advice")
    if domain == "ecommerce" and "guarantee" in lower and "refund" in lower:
        flags.append("ecommerce:no_refund_guarantee")
    if domain == "voice" and any(w in lower for w in ("are you human", "real person", "not a bot")):
        flags.append("voice:disclose_ai")
    return flags


def evaluate_guardrails(
    customer_message: str,
    reply: str,
    *,
    domain: str = "sales",
    intent: str = "general",
    confidence: float = 0.85,
) -> GuardrailResult:
    """Inspect message and reply; rewrite or force handoff when unsafe."""
    flags = _check_customer_risk(customer_message, domain)
    flags.extend(f"reply:{p}" for p in _check_reply_unsafe(reply))

    handoff_required = intent in DOMAIN_HANDOFF_INTENTS.get(domain, set())
    handoff_required = handoff_required or bool(
        any(f.startswith("customer:") for f in flags)
    )

    rewritten = reply
    if any(f.startswith("reply:") for f in flags):
        rewritten = (
            "I want to make sure you get accurate help. "
            "Let me connect you with a team member who can assist with this properly."
        )
        handoff_required = True

    if domain == "voice" and "voice:disclose_ai" in flags:
        rewritten = (
            "I'm an AI receptionist assistant. I can help route your call "
            "or arrange a callback from our team."
        )

    if confidence < 0.5:
        flags.append("low_confidence")
        handoff_required = True

    safe = not flags and not handoff_required
    status = "safe" if safe else "flagged"
    reason = "; ".join(flags[:3]) if flags else ("handoff_required" if handoff_required else "")

    return GuardrailResult(
        safe=safe,
        flags=flags,
        rewritten_reply=rewritten,
        handoff_required=handoff_required,
        reason=reason,
        status=status,
    )
