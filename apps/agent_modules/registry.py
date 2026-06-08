"""Mapping from AgentTemplate slug to agent module package and class."""
import importlib
from typing import Optional

from apps.agent_engine.base import BaseAgent

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

AGENT_CLASS_NAMES: dict[str, str] = {
    "sales-closing-agent": "SalesClosingAgent",
    "real-estate-agent": "RealEstateAgent",
    "clinic-agent": "ClinicReceptionistAgent",
    "home-services-agent": "HomeServicesAgent",
    "school-agent": "SchoolAdminAgent",
    "voice-agent": "VoiceReceptionistAgent",
    "tender-agent": "TenderProposalAgent",
    "ecommerce-agent": "EcommerceSupportAgent",
    "recruitment-agent": "RecruitmentScreeningAgent",
    "finance-agent": "FinanceAssistantAgent",
}


def get_module_path(template_slug: str) -> Optional[str]:
    """Return Python module path for a given template slug."""
    return AGENT_MODULE_MAP.get(template_slug)


def load_agent_class(template_slug: str) -> type[BaseAgent] | None:
    """Dynamically import and return the agent class for a template slug."""
    module_path = get_module_path(template_slug)
    class_name = AGENT_CLASS_NAMES.get(template_slug)
    if not module_path or not class_name:
        return None
    try:
        agent_module = importlib.import_module(f"{module_path}.agent")
        agent_cls = getattr(agent_module, class_name, None)
        if agent_cls and issubclass(agent_cls, BaseAgent):
            return agent_cls
    except ImportError:
        return None
    return None


def is_agent_implemented(template_slug: str) -> bool:
    """Return True if a working agent brain class exists for the slug."""
    return load_agent_class(template_slug) is not None


def list_implemented_slugs() -> set[str]:
    """Return all template slugs with loadable agent classes."""
    return {slug for slug in AGENT_CLASS_NAMES if load_agent_class(slug) is not None}
