"""Extract structured lead data from customer messages."""
import re
from dataclasses import dataclass, field


@dataclass
class ExtractedLeadData:
    customer_name: str = ""
    email: str = ""
    phone: str = ""
    need: str = ""
    budget: str = ""
    timeline: str = ""
    buying_intent: bool = False
    business_type: str = ""
    raw_signals: list[str] = field(default_factory=list)


class LeadExtractionService:
    """Rule-based lead field extraction from message text."""

    BUYING_INTENT_WORDS = (
        "buy", "purchase", "ready to pay", "sign up", "get started",
        "interested", "need this", "want to order",
    )
    TIMELINE_PATTERNS = (
        (r"\b(asap|immediately|urgent|this week|next week)\b", "Within 1-2 weeks"),
        (r"\b(\d+)\s*days?\b", "Within days"),
        (r"\b(\d+)\s*weeks?\b", "Within weeks"),
        (r"\bthis month\b", "This month"),
        (r"\bnext month\b", "Next month"),
        (r"\b(\d+)\s*months?\b", "Within months"),
    )
    BUDGET_PATTERN = re.compile(
        r"(\$|usd|pkr|sar|aed|€|£)\s*[\d,]+(?:\s*-\s*[\d,]+)?|\b\d+\s*-\s*\d+\s*(?:/month|per month)?",
        re.IGNORECASE,
    )

    @classmethod
    def extract(cls, message: str, existing_contact=None) -> ExtractedLeadData:
        text = message.strip()
        lower = text.lower()
        data = ExtractedLeadData()

        email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
        if email_match:
            data.email = email_match.group(0)
            data.raw_signals.append("email_shared")

        phone_match = re.search(r"\+?\d[\d\s\-()]{7,}\d", text)
        if phone_match:
            data.phone = phone_match.group(0).strip()
            data.raw_signals.append("phone_shared")

        budget_match = cls.BUDGET_PATTERN.search(text)
        if budget_match:
            data.budget = budget_match.group(0)
            data.raw_signals.append("budget_shared")

        for pattern, label in cls.TIMELINE_PATTERNS:
            if re.search(pattern, lower):
                data.timeline = label
                data.raw_signals.append("timeline_shared")
                break

        if any(w in lower for w in cls.BUYING_INTENT_WORDS):
            data.buying_intent = True
            data.raw_signals.append("buying_intent")

        if any(w in lower for w in ("demo", "call", "meeting", "schedule", "visit")):
            data.raw_signals.append("demo_interest")

        if any(w in lower for w in ("price", "pricing", "cost", "quote")):
            data.raw_signals.append("pricing_interest")

        service_keywords = ("whatsapp", "instagram", "automation", "crm", "chatbot", "sales")
        for kw in service_keywords:
            if kw in lower:
                data.need = f"Interest in {kw} solution"
                break
        if not data.need and len(text) > 20:
            data.need = text[:200]

        if existing_contact and existing_contact.name and existing_contact.name != "Web Chat Visitor":
            data.customer_name = existing_contact.name

        return data
