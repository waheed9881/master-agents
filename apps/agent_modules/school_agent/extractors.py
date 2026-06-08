from apps.agent_engine.generic.config import ExtractorConfig

EXTRACTOR_CONFIG = ExtractorConfig(
    intent_keywords={
        "admission_inquiry": ["admission", "enroll", "apply", "registration", "join"],
        "fee_inquiry": ["fee", "tuition", "cost", "payment", "scholarship"],
        "timetable_inquiry": ["timetable", "schedule", "class time", "hours"],
        "parent_complaint": ["complaint", "unhappy", "concerned", "issue with"],
        "meeting_request": ["meeting", "speak to principal", "parent teacher"],
    },
    need_keywords={
        "kindergarten": "Kindergarten admission",
        "primary": "Primary school",
        "secondary": "Secondary school",
        "academy": "Academy program",
    },
)
