"""Configurable business agent built on shared engine primitives."""

SHARED_SAFETY_PROMPT = (
    "SAFETY RULES: Never guarantee pricing, refunds, medical diagnosis, prescriptions, "
    "tax/legal/financial advice, property contracts, or final confirmed appointments. "
    "Always offer human handoff for final decisions. "
    "Do not claim live WhatsApp or Instagram connection in local mock mode."
)

from apps.agent_engine.base import BaseAgent
from apps.agent_engine.generic.config import AgentBrainConfig
from apps.agent_engine.generic.extractors import GenericExtractorMixin
from apps.agent_engine.generic.handoff import GenericHandoffMixin
from apps.agent_engine.generic.scoring import GenericScoringMixin
from apps.agent_engine.services.lead_extraction import ExtractedLeadData
from apps.crm.models import LeadStatus
from apps.crm.services import (
    create_follow_up_task,
    ensure_default_pipeline_stages,
    find_or_update_lead_for_conversation,
    update_lead,
    update_lead_score,
)
from apps.inbox.models import Conversation
from apps.inbox.services import enable_human_takeover


class GenericBusinessAgent(
    BaseAgent,
    GenericExtractorMixin,
    GenericScoringMixin,
    GenericHandoffMixin,
):
    """MVP agent with domain config — intent, CRM, handoff, knowledge."""

    brain_config: AgentBrainConfig

    @property
    def extractor_config(self):
        return self.brain_config.extractor

    @property
    def scoring_config(self):
        return self.brain_config.scoring

    @property
    def handoff_config(self):
        return self.brain_config.handoff

    def extract_lead_data(self, message: str, conversation: Conversation) -> ExtractedLeadData:
        return self.extract_domain_data(message, conversation.contact)

    def decide_handoff(self, message, intent, confidence, extracted):
        return self.evaluate_domain_handoff(message, intent, confidence, extracted)

    def decide_next_action(self, understanding: dict, ai_result: dict) -> str:
        intent = ai_result.get("intent", "")
        extracted: ExtractedLeadData = understanding["extracted"]

        if intent in self.handoff_config.handoff_intents or ai_result.get("should_handoff"):
            return "handoff"
        if intent in self.scoring_config.demo_intents:
            return "book_appointment"
        if intent in self.scoring_config.qualified_intents:
            return "qualify"
        if self.detect_hot_lead(extracted, ai_result):
            return "prioritize"
        if extracted.budget or extracted.timeline:
            return "qualify"
        return "continue_qualifying"

    def update_crm(
        self,
        conversation: Conversation,
        extracted: ExtractedLeadData,
        ai_result: dict,
    ) -> int | None:
        tenant = self.tenant
        contact = conversation.contact

        if extracted.email and not contact.email:
            contact.email = extracted.email
            contact.save(update_fields=["email", "updated_at"])
        if extracted.phone and not contact.phone:
            contact.phone = extracted.phone
            contact.save(update_fields=["phone", "updated_at"])
        if extracted.customer_name and contact.name in ("Web Chat Visitor", ""):
            contact.name = extracted.customer_name
            contact.save(update_fields=["name", "updated_at"])

        lead = find_or_update_lead_for_conversation(
            tenant,
            contact,
            agent_instance=self.agent_instance,
            conversation=conversation,
        )

        updates: dict = {}
        if extracted.need:
            updates["need"] = extracted.need
        if extracted.budget:
            updates["budget"] = extracted.budget
        if extracted.timeline:
            updates["timeline"] = extracted.timeline
        intent = ai_result.get("intent", "")
        if intent:
            updates["summary"] = f"Intent: {intent}. Last message processed."

        status = self.determine_lead_status(extracted, ai_result)
        if status:
            updates["status"] = status

        if updates:
            update_lead(lead, **updates)

        update_lead_score(lead)
        lead.refresh_from_db()

        if self.detect_hot_lead(extracted, ai_result):
            if lead.status != LeadStatus.HOT:
                update_lead(lead, status=LeadStatus.HOT)
                update_lead_score(lead)
            create_follow_up_task(lead, days_ahead=1)

        if intent in self.brain_config.follow_up_intents:
            create_follow_up_task(lead, days_ahead=2)

        if intent in self.scoring_config.demo_intents:
            update_lead(lead, status=LeadStatus.DEMO_BOOKED)
            create_follow_up_task(lead, days_ahead=1)

        ensure_default_pipeline_stages(tenant)
        return lead.pk

    def build_prompt(self, message, conversation, knowledge_context=""):
        system, user = super().build_prompt(message, conversation, knowledge_context)
        suffix = getattr(self.__class__, "prompt_suffix", "")
        extra = f"\n{suffix}" if suffix else ""
        return system + "\n" + SHARED_SAFETY_PROMPT + extra, user

    def run_with_handoff(self, message: str, conversation: Conversation):
        result = self.run(message, conversation)
        if result.should_handoff:
            enable_human_takeover(conversation)
        return result
