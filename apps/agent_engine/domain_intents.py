"""Domain intent registry — canonical intents, aliases, keywords, and priority rules."""

from __future__ import annotations

from dataclasses import dataclass

from apps.agent_engine.intent_normalizer import normalize_intent

TEMPLATE_TO_DOMAIN: dict[str, str] = {
    "sales-closing-agent": "sales",
    "real-estate-agent": "real_estate",
    "clinic-agent": "clinic",
    "home-services-agent": "home_services",
    "school-agent": "school",
    "voice-agent": "voice",
    "tender-agent": "tender",
    "ecommerce-agent": "ecommerce",
    "recruitment-agent": "recruitment",
    "finance-agent": "finance",
}


@dataclass(frozen=True)
class IntentRule:
    """Keyword rule for deterministic intent detection."""

    intent: str
    keywords: tuple[str, ...]
    priority: int = 50
    require_all: bool = False


# Safety rules — highest priority, all domains.
GLOBAL_SAFETY_RULES: tuple[IntentRule, ...] = (
    IntentRule("sensitive_topic", ("chest pain", "cannot breathe", "can't breathe", "emergency room"), 100),
    IntentRule("sensitive_topic", ("prescribe", "prescription", "take this medicine"), 98),
    IntentRule("tax_question", ("tax advice", "tax return", "corporate tax", "deduction"), 97),
    IntentRule("sensitive_topic", ("financial advice", "should i invest", "invest my savings"), 97),
    IntentRule("sensitive_topic", ("legal paperwork", "legal compliance", "regulatory compliance"), 96),
    IntentRule("pricing_scope", ("final pricing approval", "final price", "final proposal price"), 96),
    IntentRule("refund_request", ("guarantee my refund", "refund will be approved", "refund approval"), 95),
    IntentRule("handoff_request", ("speak to a manager", "speak with a human", "talk to someone"), 94),
    IntentRule("complaint", ("very angry", "terrible service", "worst experience", "unacceptable"), 93),
    IntentRule("ready_to_buy", ("ready to pay", "ready to buy", "sign up today", "make an offer"), 92),
    IntentRule("urgent_repair", ("gas leak", "flooding", "water is flooding"), 91),
    IntentRule("urgent_repair", ("emergency!", "right now!", "immediately"), 85),
)

DOMAIN_RULES: dict[str, tuple[IntentRule, ...]] = {
    "sales": (
        IntentRule("complaint", ("refund", "complaint", "angry"), 80),
        IntentRule("handoff_request", ("human", "person", "speak to"), 79),
        IntentRule("ready_to_buy", ("buy now", "purchase today", "send the contract"), 78),
        IntentRule("discount_request", ("discount", "cheaper", "lower price"), 77),
        IntentRule("demo_request", ("demo", "schedule a call", "schedule a demo"), 76),
        IntentRule("pricing_inquiry", ("how much", "pricing", "cost", "price"), 70),
        IntentRule("budget_shared", ("budget", "$", "usd", "pkr", "sar"), 65),
        IntentRule("contact_shared", ("@",), 60),
        IntentRule("greeting", ("hello", "hi", "hey", "salam"), 40),
    ),
    "real_estate": (
        IntentRule("visit_request", ("property visit", "viewing", "see the property", "schedule a visit"), 85),
        IntentRule("investment_inquiry", ("invest", "investment", "roi", "rental yield", "rental properties"), 84),
        IntentRule("ready_to_buy", ("ready to buy", "make an offer"), 83),
        IntentRule("budget_shared", ("budget", "$", "million", "thousand"), 82),
        IntentRule("location_shared", ("downtown", "marina", "neighborhood", "area", "location"), 81),
        IntentRule("property_inquiry", ("apartment", "villa", "house", "property", "bedroom", "listing"), 75),
        IntentRule("pricing_inquiry", ("how much", "price", "cost"), 60),
        IntentRule("greeting", ("hello", "hi"), 40),
    ),
    "clinic": (
        IntentRule("sensitive_topic", ("severe chest pain", "cannot breathe", "emergency"), 100),
        IntentRule("sensitive_topic", ("prescribe", "prescription"), 98),
        IntentRule("report_followup", ("lab test", "test results", "lab report", "follow up on my"), 85),
        IntentRule("symptoms_shared", ("cough", "fever", "symptom", "headache", "pain"), 80),
        IntentRule("appointment_request", ("appointment", "book", "schedule", "dental"), 75),
        IntentRule("pricing_inquiry", ("how much", "cost", "fee", "price", "consultation"), 70),
        IntentRule("greeting", ("hello", "hi"), 40),
    ),
    "home_services": (
        IntentRule("urgent_repair", ("emergency", "flooding", "gas leak", "urgent"), 90),
        IntentRule("quote_request", ("quote", "estimate", "renovation"), 80),
        IntentRule("service_request", ("plumber", "plumbing", "electrical", "repair", "fix", "leaking"), 75),
        IntentRule("location_shared", ("street", "avenue", "address", "at "), 70),
        IntentRule("budget_shared", ("budget", "$"), 65),
        IntentRule("greeting", ("hello", "hi"), 40),
    ),
    "school": (
        IntentRule("parent_complaint", ("complaint", "bullying", "unacceptable"), 88),
        IntentRule("complaint", ("complaint", "dispute", "angry"), 87),
        IntentRule("meeting_request", ("meet the principal", "meeting", "discuss admissions"), 80),
        IntentRule("timetable_inquiry", ("what time", "school start", "school end", "timetable", "class time"), 78),
        IntentRule("fee_inquiry", ("tuition", "fees", "fee"), 75),
        IntentRule("admission_inquiry", ("enroll", "admission", "grade", "registration"), 72),
        IntentRule("greeting", ("hello", "hi"), 40),
    ),
    "voice": (
        IntentRule("callback_request", ("urgent", "call me", "call me back", "callback", "immediately"), 88),
        IntentRule("complaint", ("complaint", "frustrated", "file a complaint"), 87),
        IntentRule("business_hours", ("business hours", "what time", "open", "closed", "hours today"), 85),
        IntentRule("appointment_booking", ("book an appointment", "appointment with", "appointment with sales"), 82),
        IntentRule("call_answering", ("calling about", "i am calling", "phone", "reception"), 78),
        IntentRule("callback_request", ("call me back", "callback", "+"), 75),
        IntentRule("greeting", ("hello", "hi"), 50),
    ),
    "tender": (
        IntentRule("pricing_scope", ("final pricing", "pricing approval", "legal compliance sign-off"), 95),
        IntentRule("sensitive_topic", ("regulatory compliance", "legal compliance", "contract meet"), 94),
        IntentRule("rfp_upload", ("upload", "rfp document", "rfp"), 85),
        IntentRule("requirement_extraction", ("requirements", "scope specifications", "specifications"), 84),
        IntentRule("deadline_shared", ("deadline", "submission deadline", "due date", "march"), 83),
        IntentRule("proposal_request", ("proposal", "bid", "tender", "corporate bid"), 75),
        IntentRule("greeting", ("hello", "hi"), 40),
    ),
    "ecommerce": (
        IntentRule("refund_request", ("guarantee", "refund approved", "refund will be"), 95),
        IntentRule("complaint", ("worst experience", "speak to a manager", "terrible"), 96),
        IntentRule("complaint", ("angry", "damaged", "manager"), 90),
        IntentRule("refund_request", ("refund", "money back"), 85),
        IntentRule("exchange_request", ("exchange", "larger size", "swap", "replace item"), 84),
        IntentRule("order_status", ("where is my order", "order ord", "order status", "ord-"), 83),
        IntentRule("product_question", ("waterproof", "sizes", "in stock", "product"), 75),
        IntentRule("greeting", ("hello", "hi"), 40),
    ),
    "recruitment": (
        IntentRule("salary_expectation", ("negotiate", "salary", "offer letter", "compensation", "package"), 88),
        IntentRule("interview_request", ("schedule an interview", "interview for"), 85),
        IntentRule("cv_submission", ("cv", "resume", "curriculum", "years of"), 82),
        IntentRule("availability_shared", ("start in", "can start", "notice period"), 80),
        IntentRule("job_application", ("apply for", "application", "screening questions", "position", "role"), 75),
        IntentRule("greeting", ("hello", "hi"), 40),
    ),
    "finance": (
        IntentRule("tax_question", ("tax advice", "tax return", "deduction", "filing"), 95),
        IntentRule("sensitive_topic", ("financial advice", "should i invest", "invest my savings"), 94),
        IntentRule("expense_question", ("expense", "receipt", "categorize", "reimbursement"), 85),
        IntentRule("bookkeeping_request", ("reconcile", "bookkeeping", "accounts", "ledger"), 84),
        IntentRule("payment_reminder", ("payment due", "reminder email", "when is my payment"), 83),
        IntentRule("invoice_question", ("invoice", "inv-", "billing", "statement"), 80),
        IntentRule("greeting", ("hello", "hi"), 40),
    ),
}

# Canonical intents per domain (for validation and documentation).
DOMAIN_CANONICAL_INTENTS: dict[str, frozenset[str]] = {
    domain: frozenset({normalize_intent(r.intent, domain) for r in rules} | {"general", "handoff_request", "sensitive_topic", "complaint"})
    for domain, rules in DOMAIN_RULES.items()
}


def get_domain_for_slug(template_slug: str) -> str:
    """Map agent template slug to domain key."""
    return TEMPLATE_TO_DOMAIN.get(template_slug, "sales")


def get_rules_for_domain(domain: str) -> tuple[IntentRule, ...]:
    """Return all intent rules for a domain including global safety rules."""
    domain_key = domain.strip().lower().replace(" ", "_").replace("-", "_")
    domain_rules = DOMAIN_RULES.get(domain_key, ())
    return GLOBAL_SAFETY_RULES + domain_rules


def detect_intent_from_message(domain: str, message: str) -> tuple[str, float, str]:
    """
    Deterministic intent detection from message text.

    Returns (canonical_intent, confidence, source).
    source is 'detector' when matched, 'general' when no rule matched.
    """
    lower = message.lower()
    rules = sorted(get_rules_for_domain(domain), key=lambda r: -r.priority)

    for rule in rules:
        if rule.require_all:
            if all(kw in lower for kw in rule.keywords):
                return normalize_intent(rule.intent, domain), 0.92, "detector"
        else:
            if any(kw in lower for kw in rule.keywords):
                return normalize_intent(rule.intent, domain), 0.90, "detector"

    return "general", 0.55, "general"


def resolve_final_intent(
    domain: str,
    message: str,
    provider_intent: str,
    *,
    extractor_intent: str | None = None,
) -> tuple[str, str]:
    """
    Merge provider, extractor, and detector intents into one canonical intent.

    Returns (canonical_intent, raw_intent).
    raw_intent is the pre-normalization provider intent when it differs.
    """
    detected, det_conf, _ = detect_intent_from_message(domain, message)
    norm_provider = normalize_intent(provider_intent or "general", domain)

    candidates: list[tuple[str, int]] = []

    if detected != "general":
        candidates.append((detected, 100))
    if extractor_intent:
        norm_ext = normalize_intent(extractor_intent, domain)
        if norm_ext != "general":
            candidates.append((norm_ext, 90))
    if norm_provider != "general":
        candidates.append((norm_provider, 70))

    if not candidates:
        return "general", provider_intent or "general"

    candidates.sort(key=lambda c: -c[1])
    canonical = candidates[0][0]
    raw = provider_intent or detected
    if normalize_intent(raw, domain) == canonical:
        raw = canonical
    return canonical, raw


def get_domain_keywords(domain: str) -> dict[str, list[str]]:
    """Return intent -> keywords mapping for a domain (for extractors/mock)."""
    rules = DOMAIN_RULES.get(domain, ())
    result: dict[str, list[str]] = {}
    for rule in rules:
        intent = normalize_intent(rule.intent, domain)
        result.setdefault(intent, []).extend(rule.keywords)
    return result
