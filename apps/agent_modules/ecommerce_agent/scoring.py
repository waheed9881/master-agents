from apps.agent_engine.generic.config import ScoringConfig

SCORING_CONFIG = ScoringConfig(
    hot_signal_sets=[frozenset({"complaint"}), frozenset({"refund_request"})],
    qualified_intents=frozenset({"order_status", "refund_request", "exchange_request"}),
    demo_intents=frozenset(),
)
