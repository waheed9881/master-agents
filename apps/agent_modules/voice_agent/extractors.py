from apps.agent_engine.generic.config import ExtractorConfig

EXTRACTOR_CONFIG = ExtractorConfig(
    intent_keywords={
        "call_answering": ["call", "phone", "ringing", "reception"],
        "appointment_booking": ["appointment", "book", "schedule", "reserve"],
        "business_hours": ["hours", "open", "closed", "when are you"],
        "callback_request": ["callback", "call me back", "return my call"],
        "complaint": ["complaint", "unhappy", "frustrated", "terrible"],
    },
    need_keywords={
        "sales": "Sales inquiry",
        "support": "Support inquiry",
        "billing": "Billing inquiry",
    },
)
