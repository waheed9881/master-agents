"""Generic handoff decision mixin."""
from apps.agent_engine.generic.config import HandoffConfig
from apps.agent_engine.services.handoff_decision import HandoffDecision, HandoffDecisionService
from apps.agent_engine.services.lead_extraction import ExtractedLeadData


class GenericHandoffMixin:
    """Agent-specific handoff rules layered on shared service."""

    handoff_config: HandoffConfig

    def evaluate_domain_handoff(
        self,
        message: str,
        intent: str,
        confidence: float,
        extracted: ExtractedLeadData,
    ) -> HandoffDecision:
        lower = message.lower()
        config = self.handoff_config

        if intent in config.handoff_intents:
            return HandoffDecision(True, f"intent:{intent}")

        if any(kw in lower for kw in config.safety_keywords):
            return HandoffDecision(True, "safety_keyword")

        if any(kw in lower for kw in config.urgent_keywords):
            return HandoffDecision(True, "urgent_request")

        if "handoff_request" in extracted.raw_signals:
            return HandoffDecision(True, "explicit_handoff")

        return HandoffDecisionService.evaluate(
            message,
            intent=intent,
            confidence=confidence,
            extracted_signals=extracted.raw_signals,
        )
