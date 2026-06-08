"""Sales agent module."""
from apps.agent_modules.sales_agent.agent import SalesClosingAgent

MODULE_SLUG = "sales-closing-agent"
TEMPLATE_SLUG = "sales-closing-agent"

__all__ = ["SalesClosingAgent", "MODULE_SLUG", "TEMPLATE_SLUG"]
