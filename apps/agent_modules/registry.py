"""Mapping from AgentTemplate slug to agent module package."""
from typing import Optional

AGENT_MODULE_MAP: dict[str, str] = {
    "sales-closing-agent": "apps.agent_modules.sales_agent",
    "real-estate-agent": "apps.agent_modules.real_estate_agent",
    "clinic-agent": "apps.agent_modules.clinic_agent",
    "home-services-agent": "apps.agent_modules.home_services_agent",
    "school-agent": "apps.agent_modules.school_agent",
    "voice-agent": "apps.agent_modules.voice_agent",
    "tender-agent": "apps.agent_modules.tender_agent",
    "ecommerce-agent": "apps.agent_modules.ecommerce_agent",
    "recruitment-agent": "apps.agent_modules.recruitment_agent",
    "finance-agent": "apps.agent_modules.finance_agent",
}


def get_module_path(template_slug: str) -> Optional[str]:
    """Return Python module path for a given template slug."""
    return AGENT_MODULE_MAP.get(template_slug)
