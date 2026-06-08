"""Generic domain-aware lead extraction mixin."""
import re

from apps.agent_engine.generic.config import ExtractorConfig
from apps.agent_engine.services.lead_extraction import ExtractedLeadData, LeadExtractionService


class GenericExtractorMixin:
    """Extend base lead extraction with domain-specific signals."""

    extractor_config: ExtractorConfig

    def extract_domain_data(self, message: str, existing_contact=None) -> ExtractedLeadData:
        data = LeadExtractionService.extract(message, existing_contact)
        lower = message.lower()
        config = self.extractor_config

        for intent, keywords in config.intent_keywords.items():
            if any(kw in lower for kw in keywords):
                data.raw_signals.append(intent)

        for keyword, label in config.need_keywords.items():
            if keyword in lower:
                data.need = label
                break

        for keyword, label in config.property_type_keywords.items():
            if keyword in lower:
                data.raw_signals.append(f"property_type:{label}")
                if not data.need:
                    data.need = label
                break

        if any(loc in lower for loc in config.location_keywords):
            data.raw_signals.append("location_shared")
            loc_match = re.search(
                r"(?:in|at|near)\s+([A-Za-z][A-Za-z\s]{2,30})",
                message,
                re.IGNORECASE,
            )
            if loc_match:
                data.raw_signals.append(f"location:{loc_match.group(1).strip()}")

        if any(w in lower for w in ("rent", "renting", "lease")):
            data.raw_signals.append("renting")
        if any(w in lower for w in ("buy", "buying", "purchase")):
            data.raw_signals.append("buying")

        if any(w in lower for w in ("visit", "viewing", "tour", "see the property")):
            data.raw_signals.append("visit_request")

        if any(w in lower for w in ("urgent", "emergency", "asap", "immediately")):
            data.raw_signals.append("urgent")

        order_match = re.search(r"\b(?:order|#)\s*#?(\w{5,})\b", message, re.IGNORECASE)
        if order_match:
            data.raw_signals.append(f"order_id:{order_match.group(1)}")

        invoice_match = re.search(r"\b(?:invoice|inv)[#\s-]*(\w{3,})\b", message, re.IGNORECASE)
        if invoice_match:
            data.raw_signals.append(f"invoice:{invoice_match.group(1)}")

        return data
