from apps.agent_engine.generic.config import ScoringConfig

SCORING_CONFIG = ScoringConfig(
    hot_signal_sets=[frozenset({"admission_inquiry", "phone_shared"})],
    qualified_intents=frozenset({"admission_inquiry", "meeting_request"}),
    demo_intents=frozenset({"meeting_request"}),
)
