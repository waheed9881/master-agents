"""Generic lead scoring and hot-lead detection."""
from apps.agent_engine.generic.config import ScoringConfig
from apps.agent_engine.services.lead_extraction import ExtractedLeadData
from apps.crm.models import LeadStatus


class GenericScoringMixin:
    """Score leads and determine status from extracted data."""

    scoring_config: ScoringConfig

    def detect_hot_lead(self, extracted: ExtractedLeadData, ai_result: dict) -> bool:
        signals = set(extracted.raw_signals)
        intent = ai_result.get("intent", "")
        if intent in self.scoring_config.qualified_intents:
            signals.add(intent)
        if extracted.budget:
            signals.add("budget_shared")
        if extracted.timeline:
            signals.add("timeline_shared")
        if "urgent" in signals or intent == "urgent_repair":
            return True
        for required in self.scoring_config.hot_signal_sets:
            if required.issubset(signals):
                return True
        return False

    def determine_lead_status(self, extracted: ExtractedLeadData, ai_result: dict) -> str | None:
        intent = ai_result.get("intent", "")
        if intent in self.scoring_config.demo_intents:
            return LeadStatus.DEMO_BOOKED
        if self.detect_hot_lead(extracted, ai_result):
            return LeadStatus.HOT
        if intent in self.scoring_config.qualified_intents:
            return LeadStatus.QUALIFIED
        if extracted.budget or extracted.timeline or intent.endswith("_shared"):
            return LeadStatus.QUALIFYING
        if intent == "greeting":
            return LeadStatus.NEW
        return None
