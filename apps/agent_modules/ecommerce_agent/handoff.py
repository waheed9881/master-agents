from apps.agent_engine.generic.config import HandoffConfig

HANDOFF_CONFIG = HandoffConfig(
    handoff_intents=frozenset({
        "complaint", "refund_request", "handoff_request",
    }),
    safety_keywords=("guarantee refund", "promise refund"),
    urgent_keywords=("angry", "lawyer", "sue"),
)
