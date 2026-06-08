from apps.agent_engine.generic.config import ScoringConfig

SCORING_CONFIG = ScoringConfig(
    hot_signal_sets=[frozenset({"callback_request", "phone_shared"})],
    qualified_intents=frozenset({"callback_request", "appointment_booking"}),
    demo_intents=frozenset({"appointment_booking"}),
)
