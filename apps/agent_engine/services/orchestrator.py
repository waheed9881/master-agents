"""Agent orchestration — resolve agent class and execute runs."""
import logging
from dataclasses import dataclass

from apps.agent_engine.base import AgentRunResult, BaseAgent
from apps.agent_engine.models import AgentRun, ToolCall, ToolCallStatus
from apps.agent_engine.providers.factory import get_ai_provider
from apps.agent_modules.registry import load_agent_class
from apps.agents.models import AgentInstance
from apps.inbox.models import Conversation

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorResult:
    agent_result: AgentRunResult
    agent_run_id: int


class AgentOrchestrator:
    """Resolve and run the appropriate agent for an agent instance."""

    @classmethod
    def resolve_agent(cls, agent_instance: AgentInstance) -> BaseAgent | None:
        slug = agent_instance.template.slug
        agent_cls = load_agent_class(slug)
        if not agent_cls:
            logger.warning("No agent class for slug=%s", slug)
            return None
        return agent_cls(agent_instance, provider=get_ai_provider())

    @classmethod
    def run(
        cls,
        agent_instance: AgentInstance,
        conversation: Conversation,
        customer_message: str,
    ) -> OrchestratorResult | None:
        agent = cls.resolve_agent(agent_instance)
        if not agent:
            return None

        if hasattr(agent, "run_with_handoff"):
            result = agent.run_with_handoff(customer_message, conversation)
        else:
            result = agent.run(customer_message, conversation)

        agent_run = AgentRun.objects.create(
            tenant=agent_instance.tenant,
            agent_instance=agent_instance,
            conversation=conversation,
            input_message=customer_message,
            output_message=result.reply,
            intent=result.intent,
            confidence=result.confidence,
            tokens_used=result.tokens_used,
            cost_estimate=result.cost_estimate,
        )

        if result.knowledge_used:
            ToolCall.objects.create(
                agent_run=agent_run,
                tool_name="knowledge_search",
                input_json={"query": customer_message[:200]},
                output_json={"results": result.knowledge_used},
                status=ToolCallStatus.SUCCESS,
            )

        if result.lead_id:
            ToolCall.objects.create(
                agent_run=agent_run,
                tool_name="update_crm",
                input_json={"lead_id": result.lead_id},
                output_json={"lead_id": result.lead_id},
                status=ToolCallStatus.SUCCESS,
            )

        if result.should_handoff:
            ToolCall.objects.create(
                agent_run=agent_run,
                tool_name="handoff",
                input_json={"reason": result.handoff_reason},
                output_json={"handoff": True},
                status=ToolCallStatus.SUCCESS,
            )

        return OrchestratorResult(agent_result=result, agent_run_id=agent_run.pk)
