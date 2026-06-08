from apps.agent_engine.generic.config import ScoringConfig

SCORING_CONFIG = ScoringConfig(
    hot_signal_sets=[
        frozenset({"interview_request", "cv_submission"}),
        frozenset({"job_application", "salary_expectation"}),
    ],
    qualified_intents=frozenset({"interview_request", "job_application"}),
    demo_intents=frozenset({"interview_request"}),
)
