from apps.agent_engine.generic.config import ExtractorConfig

EXTRACTOR_CONFIG = ExtractorConfig(
    intent_keywords={
        "service_request": ["plumbing", "electrical", "repair", "renovation", "install", "fix"],
        "location_shared": ["address", "location", "city", "area", "street"],
        "budget_shared": ["budget", "$", "quote", "estimate", "cost"],
        "urgent_repair": ["urgent", "emergency", "leak", "flooding", "no power", "broken"],
        "quote_request": ["quote", "estimate", "bid", "pricing"],
    },
    need_keywords={
        "plumbing": "Plumbing service",
        "electrical": "Electrical service",
        "hvac": "HVAC service",
        "renovation": "Renovation project",
        "painting": "Painting service",
    },
    location_keywords=("street", "avenue", "block", "city", "address"),
)
