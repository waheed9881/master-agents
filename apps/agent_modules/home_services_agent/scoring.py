from apps.agent_engine.generic.config import ScoringConfig

SCORING_CONFIG = ScoringConfig(
    hot_signal_sets=[
        frozenset({"urgent_repair"}),
        frozenset({"quote_request", "location_shared"}),
    ],
    qualified_intents=frozenset({"quote_request", "urgent_repair"}),
    demo_intents=frozenset(),
)
