from apps.agent_engine.generic.config import HandoffConfig

HANDOFF_CONFIG = HandoffConfig(
    handoff_intents=frozenset({
        "handoff_request", "complaint", "pricing_scope",
    }),
    safety_keywords=("legal compliance", "contract law", "regulatory"),
    urgent_keywords=("deadline tomorrow", "due today"),
)
