from apps.agent_engine.generic.config import HandoffConfig

HANDOFF_CONFIG = HandoffConfig(
    handoff_intents=frozenset({"complaint", "handoff_request", "urgent_repair"}),
    safety_keywords=("gas leak", "electrical fire", "structural damage", "safety hazard"),
    urgent_keywords=("emergency", "flooding", "gas leak", "no power"),
)
