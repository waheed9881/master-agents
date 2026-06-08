from apps.agent_engine.generic.business_agent import GenericBusinessAgent
from apps.agent_engine.generic.config import AgentBrainConfig

from .extractors import EXTRACTOR_CONFIG
from .handoff import HANDOFF_CONFIG
from .prompts import PROMPT_SUFFIX
from .scoring import SCORING_CONFIG


class VoiceReceptionistAgent(GenericBusinessAgent):
    template_slug = "voice-agent"
    brain_config = AgentBrainConfig(
        template_slug="voice-agent",
        extractor=EXTRACTOR_CONFIG,
        scoring=SCORING_CONFIG,
        handoff=HANDOFF_CONFIG,
        lead_title_prefix="Reception inquiry",
        follow_up_intents=frozenset({"callback_request", "appointment_booking"}),
    )

    def build_prompt(self, message, conversation, knowledge_context=""):
        system, user = super().build_prompt(message, conversation, knowledge_context)
        return system + "\n" + PROMPT_SUFFIX, user
