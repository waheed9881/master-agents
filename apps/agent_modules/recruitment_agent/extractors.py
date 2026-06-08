from apps.agent_engine.generic.config import ExtractorConfig

EXTRACTOR_CONFIG = ExtractorConfig(
    intent_keywords={
        "job_application": ["apply", "application", "job", "position", "role"],
        "cv_submission": ["cv", "resume", "curriculum"],
        "interview_request": ["interview", "meet", "schedule interview"],
        "salary_expectation": ["salary", "compensation", "pay", "package"],
        "availability_shared": ["available", "start date", "notice period", "join"],
    },
    need_keywords={
        "developer": "Developer role",
        "manager": "Manager role",
        "sales": "Sales role",
        "designer": "Designer role",
    },
)
