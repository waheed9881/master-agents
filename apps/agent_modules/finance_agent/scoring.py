from apps.agent_engine.generic.config import ScoringConfig

SCORING_CONFIG = ScoringConfig(
    hot_signal_sets=[frozenset({"payment_reminder", "invoice_question"})],
    qualified_intents=frozenset({"invoice_question", "bookkeeping_request"}),
    demo_intents=frozenset(),
)
