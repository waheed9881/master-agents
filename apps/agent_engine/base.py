"""Base agent interface for all agent modules."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from apps.agent_engine.domain_intents import detect_intent_from_message, get_domain_for_slug, resolve_final_intent
from apps.agent_engine.providers.base import AIProviderAdapter
from apps.agent_engine.providers.factory import get_ai_provider
from apps.agent_engine.services.handoff_decision import HandoffDecision
from apps.agent_engine.services.safety_guardrails import evaluate_guardrails
from apps.agent_engine.structured_output import structured_from_completion
from apps.agent_engine.services.knowledge_search import KnowledgeSearchService
from apps.agent_engine.services.lead_extraction import ExtractedLeadData, LeadExtractionService
from apps.agent_engine.services.prompt_builder import PromptBuilder
from apps.agents.models import AgentInstance
from apps.inbox.models import Conversation, Message


@dataclass
class AgentRunResult:
    reply: str
    intent: str = "general"
    raw_intent: str = ""
    confidence: float = 0.0
    tokens_used: int = 0
    cost_estimate: float = 0.0
    extracted_lead: ExtractedLeadData = field(default_factory=ExtractedLeadData)
    handoff: HandoffDecision = field(default_factory=lambda: HandoffDecision(False))
    knowledge_used: list[dict] = field(default_factory=list)
    lead_id: int | None = None
    should_handoff: bool = False
    handoff_reason: str = ""
    provider_name: str = "mock"
    model_name: str = ""
    fallback_used: bool = False
    safety_status: str = "safe"
    structured_output: dict = field(default_factory=dict)
    run_metadata: dict = field(default_factory=dict)


class BaseAgent(ABC):
    """Shared interface every agent module must implement."""

    template_slug: str = ""

    def __init__(self, agent_instance: AgentInstance, provider: AIProviderAdapter | None = None):
        self.agent_instance = agent_instance
        self.provider = provider or get_ai_provider()
        self.tenant = agent_instance.tenant

    def _get_template_slug(self) -> str:
        if getattr(self, "template_slug", ""):
            return self.template_slug
        brain_config = getattr(self, "brain_config", None)
        if brain_config and getattr(brain_config, "template_slug", ""):
            return brain_config.template_slug
        return self.agent_instance.template.slug

    def understand_message(self, message: str, conversation: Conversation) -> dict:
        """Analyze customer message intent and signals."""
        extracted = self.extract_lead_data(message, conversation)
        domain = get_domain_for_slug(self._get_template_slug())
        detected, _, _ = detect_intent_from_message(domain, message)
        if detected != "general":
            extracted.detected_intent = detected
            if f"intent:{detected}" not in extracted.raw_signals:
                extracted.raw_signals.append(f"intent:{detected}")
        return {
            "message": message,
            "extracted": extracted,
            "contact_id": conversation.contact_id,
            "domain": domain,
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

    def generate_reply(self, system_prompt: str, user_prompt: str, *, customer_message: str = "", domain: str = "sales") -> dict:
        """Call AI provider and return completion dict."""
        result = self.provider.complete(system_prompt, user_prompt)
        structured = structured_from_completion(
            result,
            domain=domain,
            customer_message=customer_message,
        )
        meta = dict(result.metadata or {})
        return {
            "text": structured.reply_text or result.text,
            "intent": structured.intent or result.intent,
            "confidence": structured.confidence or result.confidence,
            "tokens_used": result.tokens_used,
            "cost_estimate": float(result.cost_estimate),
            "provider_name": meta.get("provider_resolved") or meta.get("provider") or getattr(self.provider, "provider_name", "mock"),
            "model_name": meta.get("model", ""),
            "fallback_used": bool(meta.get("fallback_used")),
            "structured_output": structured.to_dict(),
            "raw_provider_text": result.text,
            "run_metadata": meta,
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

        domain = understanding.get("domain") or get_domain_for_slug(self._get_template_slug())
        system_prompt, user_prompt = self.build_prompt(message, conversation, knowledge_context)
        ai_result = self.generate_reply(system_prompt, user_prompt, customer_message=message, domain=domain)
        canonical_intent, raw_intent = resolve_final_intent(
            domain,
            message,
            ai_result.get("intent", "general"),
            extractor_intent=extracted.detected_intent or None,
        )
        ai_result["intent"] = canonical_intent
        ai_result["raw_intent"] = raw_intent if raw_intent != canonical_intent else ""

        guardrails = evaluate_guardrails(
            message,
            ai_result.get("text", ""),
            domain=domain,
            intent=ai_result.get("intent", "general"),
            confidence=ai_result.get("confidence", 0.0),
        )
        if not guardrails.safe:
            from apps.tenants.audit import log_audit_event

            log_audit_event(
                action="unsafe_guardrail_triggered",
                tenant=conversation.tenant,
                object_type="conversation",
                object_id=conversation.pk,
                metadata={
                    "flags": guardrails.flags,
                    "reason": guardrails.reason,
                    "domain": domain,
                },
            )

        handoff = self.decide_handoff(
            message,
            ai_result.get("intent", ""),
            ai_result.get("confidence", 0.0),
            extracted,
        )
        if guardrails.handoff_required:
            handoff = HandoffDecision(True, guardrails.reason or "safety_guardrail")

        reply = guardrails.rewritten_reply or ai_result["text"]
        if handoff.should_handoff and "connect you" not in reply.lower():
            reply += (
                "\n\nI'll connect you with a team member who can help with this."
            )

        lead_id = self.update_crm(conversation, extracted, ai_result)
        next_action = self.decide_next_action(understanding, ai_result)

        return AgentRunResult(
            reply=reply,
            intent=ai_result.get("intent", "general"),
            raw_intent=ai_result.get("raw_intent", ""),
            confidence=ai_result.get("confidence", 0.0),
            tokens_used=ai_result.get("tokens_used", 0),
            cost_estimate=ai_result.get("cost_estimate", 0.0),
            extracted_lead=extracted,
            handoff=handoff,
            knowledge_used=knowledge_results,
            lead_id=lead_id,
            should_handoff=handoff.should_handoff,
            handoff_reason=handoff.reason,
            provider_name=ai_result.get("provider_name", "mock"),
            model_name=ai_result.get("model_name", ""),
            fallback_used=ai_result.get("fallback_used", False),
            safety_status=guardrails.status,
            structured_output=ai_result.get("structured_output", {}),
            run_metadata={
                **ai_result.get("run_metadata", {}),
                "safety_flags": guardrails.flags,
                "raw_provider_text": ai_result.get("raw_provider_text", ""),
            },
        )
