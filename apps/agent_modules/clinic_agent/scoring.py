from apps.agent_engine.generic.config import ScoringConfig

SCORING_CONFIG = ScoringConfig(
    hot_signal_sets=[frozenset({"appointment_request", "phone_shared"})],
    qualified_intents=frozenset({"appointment_request"}),
    demo_intents=frozenset({"appointment_request"}),
)
