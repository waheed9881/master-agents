from apps.agent_engine.generic.config import ScoringConfig

SCORING_CONFIG = ScoringConfig(
    hot_signal_sets=[
        frozenset({"budget_shared", "location_shared", "visit_request"}),
        frozenset({"ready_to_buy"}),
    ],
    qualified_intents=frozenset({"visit_request", "ready_to_buy", "investment_inquiry"}),
    demo_intents=frozenset({"visit_request"}),
)
