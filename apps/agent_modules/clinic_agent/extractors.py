from apps.agent_engine.generic.config import ExtractorConfig

EXTRACTOR_CONFIG = ExtractorConfig(
    intent_keywords={
        "appointment_request": ["appointment", "book", "schedule", "see doctor", "visit clinic"],
        "symptoms_shared": ["symptom", "pain", "fever", "cough", "headache", "feeling"],
        "doctor_availability": ["available", "doctor", "specialist", "when can"],
        "pricing_inquiry": ["price", "cost", "fee", "how much", "charges"],
        "report_followup": ["report", "test result", "lab", "follow up"],
    },
    need_keywords={
        "dental": "Dental service",
        "cardiology": "Cardiology",
        "pediatric": "Pediatrics",
        "dermatology": "Dermatology",
        "general": "General consultation",
    },
)
