from apps.agent_engine.generic.config import HandoffConfig

HANDOFF_CONFIG = HandoffConfig(
    handoff_intents=frozenset({
        "handoff_request", "complaint", "salary_expectation",
    }),
    safety_keywords=("offer letter", "sign contract"),
    urgent_keywords=("offer", "negotiate salary"),
)
