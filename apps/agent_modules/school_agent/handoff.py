from apps.agent_engine.generic.config import HandoffConfig

HANDOFF_CONFIG = HandoffConfig(
    handoff_intents=frozenset({
        "parent_complaint", "handoff_request", "complaint",
    }),
    safety_keywords=("fee dispute", "bullying", "harassment"),
    urgent_keywords=("complaint", "bullying"),
)
