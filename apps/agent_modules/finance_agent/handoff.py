from apps.agent_engine.generic.config import HandoffConfig

HANDOFF_CONFIG = HandoffConfig(
    handoff_intents=frozenset({
        "tax_question", "handoff_request", "complaint",
    }),
    safety_keywords=(
        "tax advice", "legal advice", "financial advice",
        "invest", "tax return", "audit opinion",
    ),
    urgent_keywords=("audit", "irs", "penalty"),
)
