from apps.agent_engine.generic.config import HandoffConfig

HANDOFF_CONFIG = HandoffConfig(
    handoff_intents=frozenset({"complaint", "handoff_request"}),
    safety_keywords=(),
    urgent_keywords=("urgent", "emergency"),
)
