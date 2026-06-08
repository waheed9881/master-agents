"""Base agent interface for all agent modules."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from apps.agent_engine.providers.base import AIProviderAdapter
from apps.agent_engine.providers.factory import get_ai_provider
from apps.agent_engine.services.handoff_decision import HandoffDecision
from apps.agent_engine.services.knowledge_search import KnowledgeSearchService
from apps.agent_engine.services.lead_extraction import ExtractedLeadData, LeadExtractionService
from apps.agent_engine.services.prompt_builder import PromptBuilder
from apps.agents.models import AgentInstance
from apps.inbox.models import Conversation, Message


@dataclass
class AgentRunResult:
    reply: str
    intent: str = "general"
    confidence: float = 0.0
    tokens_used: int = 0
    cost_estimate: float = 0.0
    extracted_lead: ExtractedLeadData = field(default_factory=ExtractedLeadData)
    handoff: HandoffDecision = field(default_factory=lambda: HandoffDecision(False))
    knowledge_used: list[dict] = field(default_factory=list)
    lead_id: int | None = None
    should_handoff: bool = False
    handoff_reason: str = ""


class BaseAgent(ABC):
    """Shared interface every agent module must implement."""

    template_slug: str = ""

    def __init__(self, agent_instance: AgentInstance, provider: AIProviderAdapter | None = None):
        self.agent_instance = agent_instance
        self.provider = provider or get_ai_provider()
        self.tenant = agent_instance.tenant

    def understand_message(self, message: str, conversation: Conversation) -> dict:
        """Analyze customer message intent and signals."""
        extracted = self.extract_lead_data(message, conversation)
        return {
            "message": message,
            "extracted": extracted,
            "contact_id": conversation.contact_id,
        }

    def build_prompt(
        self,
        message: str,
        conversation: Conversation,
        knowledge_context: str = "",
    ) -> tuple[str, str]:
        """Return (system_prompt, user_prompt)."""
        system = PromptBuilder.build_system_prompt(self.agent_instance, knowledge_context)
        recent = list(
            conversation.messages.order_by("-created_at").values_list("message_text", flat=True)[:6]
        )
        user = PromptBuilder.build_user_prompt(message, conversation, recent_messages=recent[::-1])
        return system, user

    def generate_reply(self, system_prompt: str, user_prompt: str) -> dict:
        """Call AI provider and return completion dict."""
        result = self.provider.complete(system_prompt, user_prompt)
        return {
            "text": result.text,
            "intent": result.intent,
            "confidence": result.confidence,
            "tokens_used": result.tokens_used,
            "cost_estimate": float(result.cost_estimate),
        }

    def extract_lead_data(self, message: str, conversation: Conversation) -> ExtractedLeadData:
        return LeadExtractionService.extract(message, conversation.contact)

    @abstractmethod
    def decide_next_action(self, understanding: dict, ai_result: dict) -> str:
        """Return next action label e.g. qualify, book_demo, handoff."""

    @abstractmethod
    def update_crm(self, conversation: Conversation, extracted: ExtractedLeadData, ai_result: dict) -> int | None:
        """Create or update CRM lead. Returns lead_id."""

    def decide_handoff(
        self,
        message: str,
        intent: str,
        confidence: float,
        extracted: ExtractedLeadData,
    ) -> HandoffDecision:
        from apps.agent_engine.services.handoff_decision import HandoffDecisionService

        return HandoffDecisionService.evaluate(
            message,
            intent=intent,
            confidence=confidence,
            extracted_signals=extracted.raw_signals,
        )

    def search_knowledge(self, query: str) -> list[dict]:
        return KnowledgeSearchService.search(self.agent_instance, query)

    def run(self, message: str, conversation: Conversation) -> AgentRunResult:
        """Full agent pipeline."""
        understanding = self.understand_message(message, conversation)
        extracted = understanding["extracted"]

        knowledge_results = self.search_knowledge(message)
        knowledge_context = KnowledgeSearchService.format_context(knowledge_results)

        system_prompt, user_prompt = self.build_prompt(message, conversation, knowledge_context)
        ai_result = self.generate_reply(system_prompt, user_prompt)

        handoff = self.decide_handoff(
            message,
            ai_result.get("intent", ""),
            ai_result.get("confidence", 0.0),
            extracted,
        )

        reply = ai_result["text"]
        if handoff.should_handoff and "connect you" not in reply.lower():
            reply += (
                "\n\nI'll connect you with a team member who can help with this."
            )

        lead_id = self.update_crm(conversation, extracted, ai_result)
        next_action = self.decide_next_action(understanding, ai_result)

        return AgentRunResult(
            reply=reply,
            intent=ai_result.get("intent", "general"),
            confidence=ai_result.get("confidence", 0.0),
            tokens_used=ai_result.get("tokens_used", 0),
            cost_estimate=ai_result.get("cost_estimate", 0.0),
            extracted_lead=extracted,
            handoff=handoff,
            knowledge_used=knowledge_results,
            lead_id=lead_id,
            should_handoff=handoff.should_handoff,
            handoff_reason=handoff.reason,
        )
