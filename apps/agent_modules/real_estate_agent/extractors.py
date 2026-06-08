from apps.agent_engine.generic.config import ExtractorConfig

EXTRACTOR_CONFIG = ExtractorConfig(
    intent_keywords={
        "property_inquiry": ["property", "apartment", "house", "villa", "flat", "listing"],
        "budget_shared": ["budget", "$", "usd", "million", "thousand"],
        "location_shared": ["location", "area", "neighborhood", "downtown", "suburb"],
        "visit_request": ["visit", "viewing", "tour", "see the property", "schedule visit"],
        "investment_inquiry": ["invest", "investment", "roi", "rental yield"],
        "ready_to_buy": ["ready to buy", "make an offer", "purchase now"],
    },
    need_keywords={
        "apartment": "Apartment inquiry",
        "villa": "Villa inquiry",
        "house": "House inquiry",
        "commercial": "Commercial property inquiry",
    },
    location_keywords=("downtown", "suburb", "marina", "district", "city"),
    property_type_keywords={
        "apartment": "Apartment",
        "villa": "Villa",
        "house": "House",
        "condo": "Condo",
        "commercial": "Commercial",
    },
)
