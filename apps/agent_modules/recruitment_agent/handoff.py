from apps.agent_engine.generic.config import HandoffConfig

HANDOFF_CONFIG = HandoffConfig(
    handoff_intents=frozenset({
        "handoff_request", "complaint",
    }),
    safety_keywords=("offer letter", "sign contract"),
    urgent_keywords=("offer letter", "negotiate", "negotiate salary"),
)
