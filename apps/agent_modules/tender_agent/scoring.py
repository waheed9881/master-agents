from apps.agent_engine.generic.config import ScoringConfig

SCORING_CONFIG = ScoringConfig(
    hot_signal_sets=[frozenset({"proposal_request", "deadline_shared"})],
    qualified_intents=frozenset({"proposal_request", "rfp_upload"}),
    demo_intents=frozenset(),
)
