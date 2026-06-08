from apps.agent_engine.generic.config import HandoffConfig

HANDOFF_CONFIG = HandoffConfig(
    handoff_intents=frozenset({
        "ready_to_buy", "handoff_request", "complaint",
    }),
    safety_keywords=("legal paperwork", "final price", "contract", "lawyer"),
    urgent_keywords=("ready to buy", "make an offer"),
)
