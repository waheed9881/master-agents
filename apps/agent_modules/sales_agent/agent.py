"""Sales closing agent — WhatsApp + Instagram + web chat MVP."""
from apps.agent_engine.base import BaseAgent
from apps.agent_engine.services.lead_extraction import ExtractedLeadData
from apps.crm.models import LeadStatus
from apps.crm.services import (
    create_follow_up_task,
    detect_hot_lead,
    ensure_default_pipeline_stages,
    find_or_update_lead_for_conversation,
    update_lead,
    update_lead_score,
)
from apps.inbox.models import Conversation
from apps.inbox.services import enable_human_takeover


class SalesClosingAgent(BaseAgent):
    """Qualify leads, answer from knowledge, score, and hand off when needed."""

    template_slug = "sales-closing-agent"

    def decide_next_action(self, understanding: dict, ai_result: dict) -> str:
        intent = ai_result.get("intent", "")
        extracted: ExtractedLeadData = understanding["extracted"]

        if intent in ("handoff_request", "complaint", "ready_to_buy", "sensitive_topic"):
            return "handoff"
        if intent == "demo_request" or "demo_interest" in extracted.raw_signals:
            return "book_demo"
        if intent == "pricing_inquiry" or "pricing_interest" in extracted.raw_signals:
            return "share_pricing"
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

        updates = {}
        if extracted.need:
            updates["need"] = extracted.need
        if extracted.budget:
            updates["budget"] = extracted.budget
        if extracted.timeline:
            updates["timeline"] = extracted.timeline
        if ai_result.get("intent"):
            updates["summary"] = f"Intent: {ai_result['intent']}. Last message processed."

        status = self._determine_lead_status(extracted, ai_result)
        if status:
            updates["status"] = status

        if updates:
            update_lead(lead, **updates)

        update_lead_score(lead)
        lead.refresh_from_db()

        if detect_hot_lead(lead, extracted, ai_result.get("intent", "")):
            if lead.status != LeadStatus.HOT:
                update_lead(lead, status=LeadStatus.HOT)
                update_lead_score(lead)
            create_follow_up_task(lead, days_ahead=1)

        if ai_result.get("intent") == "demo_request":
            update_lead(lead, status=LeadStatus.DEMO_BOOKED)
            create_follow_up_task(lead, days_ahead=1)

        ensure_default_pipeline_stages(tenant)
        return lead.pk

    def _determine_lead_status(self, extracted: ExtractedLeadData, ai_result: dict) -> str | None:
        intent = ai_result.get("intent", "")
        if intent == "demo_request":
            return LeadStatus.DEMO_BOOKED
        if extracted.budget and extracted.timeline:
            return LeadStatus.QUALIFIED
        if extracted.budget or extracted.timeline or "pricing_interest" in extracted.raw_signals:
            return LeadStatus.QUALIFYING
        if intent == "greeting":
            return LeadStatus.NEW
        return None

    def run_with_handoff(self, message: str, conversation: Conversation):
        """Run agent and trigger inbox handoff if needed."""
        result = self.run(message, conversation)
        if result.should_handoff:
            enable_human_takeover(conversation)
        return result
