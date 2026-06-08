from apps.agent_engine.generic.config import HandoffConfig

HANDOFF_CONFIG = HandoffConfig(
    handoff_intents=frozenset({
        "complaint", "handoff_request", "sensitive_topic",
    }),
    safety_keywords=(
        "diagnose", "prescribe", "medicine", "medication",
        "chest pain", "can't breathe", "emergency", "severe bleeding",
    ),
    urgent_keywords=("emergency", "severe", "can't breathe", "chest pain"),
)
