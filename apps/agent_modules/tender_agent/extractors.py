from apps.agent_engine.generic.config import ExtractorConfig

EXTRACTOR_CONFIG = ExtractorConfig(
    intent_keywords={
        "rfp_upload": ["rfp", "tender document", "upload", "attachment"],
        "proposal_request": ["proposal", "bid", "submission", "tender"],
        "requirement_extraction": ["requirements", "scope", "specifications"],
        "deadline_shared": ["deadline", "due date", "submit by", "closing date"],
        "pricing_scope": ["pricing", "budget", "cost estimate", "fee"],
    },
    need_keywords={
        "government": "Government tender",
        "corporate": "Corporate RFP",
        "construction": "Construction tender",
    },
)
