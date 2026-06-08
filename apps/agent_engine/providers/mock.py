"""Deterministic mock AI provider for local demo and testing."""
import re

from apps.agent_engine.domain_intents import detect_intent_from_message, get_domain_for_slug
from apps.agent_engine.intent_normalizer import normalize_intent
from apps.agent_engine.providers.base import AICompletionResult, AIProviderAdapter
from apps.agent_engine.structured_output import build_mock_structured
from apps.agent_engine.services.provider_settings import get_model_name

DOMAIN_REPLY_STYLES: dict[str, dict[str, str]] = {
    "sales": {
        "greeting": (
            "Hello! Welcome to {business}. I'm here to help you find the right solution. "
            "What service are you looking for today?"
        ),
        "pricing_inquiry": (
            "I'd be happy to discuss pricing. {pricing_hint}"
            "Could you share your budget range and timeline so I can recommend the best fit?"
        ),
        "demo_request": (
            "I'd love to schedule a demo for you. What day and time works best, "
            "and what's the best email or phone to confirm?"
        ),
        "ready_to_buy": (
            "That's great to hear! I'll have our sales team send you the next steps. "
            "A team member will confirm final details with you shortly."
        ),
        "complaint": (
            "I'm sorry to hear you're frustrated. I'll connect you with a team member "
            "who can assist you directly."
        ),
        "handoff_request": (
            "Of course — I'll arrange for a team member to follow up shortly. "
            "Could you confirm the best phone number or email?"
        ),
        "default": (
            "Thanks for reaching out. To help you better, could you tell me what service "
            "you need, your business type, budget range, and timeline?"
        ),
    },
    "real_estate": {
        "property_inquiry": (
            "I'd be happy to help with your property search. What type of property, "
            "which area, and what is your budget?"
        ),
        "budget_shared": (
            "Thank you for sharing your budget. I'll note your preferences and "
            "a licensed agent can match suitable listings for you."
        ),
        "location_shared": (
            "Noted on your preferred location. What property type and budget range "
            "should we focus on?"
        ),
        "visit_request": (
            "I can help arrange a property viewing. Please share your preferred date/time "
            "and contact number — our team will confirm availability."
        ),
        "investment_inquiry": (
            "I can share general information about investment properties in your area. "
            "Returns vary by market — a licensed agent will discuss options with you."
        ),
        "ready_to_buy": (
            "Great — I'll connect you with a licensed agent to discuss your offer "
            "and next steps."
        ),
        "default": (
            "How can I help with your property search? Share the type, location, and budget "
            "you're considering."
        ),
    },
    "clinic": {
        "appointment_request": (
            "I can help schedule an appointment. Please share your name, phone number, "
            "preferred date/time, and department — staff will confirm the booking."
        ),
        "symptoms_shared": (
            "I understand you're not feeling well. I cannot provide a diagnosis. "
            "Please share your symptoms and preferred appointment time — our staff will follow up."
        ),
        "pricing_inquiry": (
            "Consultation fees vary by service. I'll share general fee information; "
            "our front desk can confirm exact pricing for your visit."
        ),
        "sensitive_topic": (
            "This sounds urgent. Please seek immediate medical attention if needed. "
            "I'm connecting you with our clinic staff right away."
        ),
        "report_followup": (
            "I can help with your lab report follow-up. I'll create a request for our "
            "medical staff to review your results and contact you."
        ),
        "default": (
            "How may I help you today? I can assist with appointments, services, "
            "or general clinic information."
        ),
    },
    "home_services": {
        "service_request": (
            "I can help with your service request. What type of work do you need, "
            "your address, and when would you like someone to visit?"
        ),
        "urgent_repair": (
            "This sounds urgent. I'm escalating this to our dispatch team immediately. "
            "Please share your address and phone number."
        ),
        "quote_request": (
            "I can start a quote request for you. Please describe the scope of work, "
            "share photos if possible, and your location — an estimator will follow up."
        ),
        "budget_shared": (
            "Thank you for sharing your budget. Our team will review the scope "
            "and contact you with an estimate — final pricing requires human confirmation."
        ),
        "default": (
            "What service do you need? Share the issue, your location, and preferred timing."
        ),
    },
    "school": {
        "admission_inquiry": (
            "Thank you for your interest! What grade or program are you inquiring about, "
            "and could you share a parent contact number?"
        ),
        "fee_inquiry": (
            "I can share general tuition information from our fee schedule. "
            "Our admissions office can confirm current rates for your grade level."
        ),
        "timetable_inquiry": (
            "School hours and timetables vary by grade level. "
            "I can share general schedules — the office can confirm your child's specific timetable."
        ),
        "parent_complaint": (
            "I'm sorry to hear about your concern. This requires attention from our staff. "
            "I'll connect you with the appropriate administrator."
        ),
        "meeting_request": (
            "I can request a meeting with the principal. Please share your name, "
            "child's grade, and preferred dates — staff will confirm scheduling."
        ),
        "complaint": (
            "I understand this is important. I'll connect you with school administration "
            "to address your concern."
        ),
        "default": (
            "How can I help? I can assist with admissions, fees, schedules, or general inquiries."
        ),
    },
    "voice": {
        "business_hours": (
            "Our business hours are available in our knowledge base. "
            "I can have someone confirm today's hours if needed."
        ),
        "callback_request": (
            "I can arrange a callback. Please confirm your name, phone number, "
            "and reason for the call."
        ),
        "appointment_booking": (
            "I can request an appointment for you. Please share preferred date/time "
            "and contact details — staff will confirm the booking."
        ),
        "call_answering": (
            "Thank you for calling {business}. How may I direct your call today?"
        ),
        "complaint": (
            "I'm sorry for the trouble. I'll connect you with a team member "
            "who can help resolve this."
        ),
        "greeting": (
            "Hello, {business}. How may I help you today?"
        ),
        "default": (
            "How may I assist you? I can help with hours, callbacks, or appointments."
        ),
    },
    "tender": {
        "rfp_upload": (
            "I can help with your RFP submission. Please share the document, "
            "project type, and submission deadline."
        ),
        "proposal_request": (
            "I can help prepare a proposal outline. Please share the RFP requirements, "
            "scope, and deadline — our bid team will follow up."
        ),
        "deadline_shared": (
            "Deadline noted. I'll list the required documents from our checklist. "
            "Our proposal team will confirm completeness."
        ),
        "requirement_extraction": (
            "Thank you for the requirements. I'll capture the scope details "
            "for our proposal team to review."
        ),
        "pricing_scope": (
            "Final pricing and compliance sign-off require human approval. "
            "I'll connect you with our bid manager."
        ),
        "sensitive_topic": (
            "Legal and compliance questions require specialist review. "
            "I'll connect you with our compliance team."
        ),
        "default": (
            "How can I help with your tender or proposal? Share the RFP, deadline, "
            "and key requirements."
        ),
    },
    "ecommerce": {
        "order_status": (
            "I can help track your order. Please confirm your order ID and "
            "the email or phone on the order."
        ),
        "refund_request": (
            "I understand you'd like a refund. Refund decisions are reviewed by our team — "
            "I'll escalate this for human confirmation."
        ),
        "exchange_request": (
            "I can start an exchange request. Please share your order ID, item details, "
            "and preferred replacement — staff will confirm eligibility."
        ),
        "product_question": (
            "I can help with product details from our catalog. "
            "Let me check specifications and availability for you."
        ),
        "complaint": (
            "I'm sorry for the poor experience. I'll connect you with a support specialist "
            "who can help resolve this."
        ),
        "default": (
            "How can I help? I can assist with orders, products, exchanges, or returns."
        ),
    },
    "recruitment": {
        "job_application": (
            "Thank you for your interest! Which role are you applying for, "
            "and could you share your experience and availability?"
        ),
        "cv_submission": (
            "Thank you for sharing your CV. I'll note your experience — "
            "our recruiting team will review and follow up."
        ),
        "interview_request": (
            "I can request an interview slot for you. Please share your preferred times "
            "and role — HR will confirm scheduling."
        ),
        "salary_expectation": (
            "Salary and offer discussions are handled by our HR team. "
            "I'll connect you with a recruiter to discuss compensation."
        ),
        "availability_shared": (
            "Thank you for sharing your availability and expectations. "
            "Our recruiting team will review and follow up."
        ),
        "default": (
            "How can I help with your application? Share the role you're interested in "
            "and your background."
        ),
    },
    "finance": {
        "invoice_question": (
            "I can help with your invoice inquiry. Please share the invoice number, "
            "amount, and due date — our accounts team will follow up."
        ),
        "payment_reminder": (
            "I can help with payment timing. Please share the invoice reference "
            "and I'll create a follow-up for our accounts team."
        ),
        "expense_question": (
            "I can provide general expense categorization guidance. "
            "For specific tax treatment, our bookkeeper will confirm with you."
        ),
        "bookkeeping_request": (
            "I can request account reconciliation assistance. "
            "Our bookkeeping team will review and contact you."
        ),
        "tax_question": (
            "I'm not able to answer tax filing or deduction questions. "
            "I'll connect you with a qualified tax professional on our team."
        ),
        "sensitive_topic": (
            "I'm not able to recommend investments or provide personalized guidance. "
            "I'll connect you with a licensed advisor."
        ),
        "default": (
            "How can I help? I can assist with invoices, payments, expenses, or bookkeeping requests."
        ),
    },
}


class MockAIProvider(AIProviderAdapter):
    """Rule-based provider returning domain-aware assistant responses."""

    provider_name = "mock"

    def complete(self, system_prompt: str, user_prompt: str, **kwargs) -> AICompletionResult:
        message = self._extract_customer_message(user_prompt)
        business = self._extract_business_name(system_prompt)
        domain = self._extract_domain(system_prompt)
        pricing_hint = self._extract_pricing_hint(system_prompt)

        intent, confidence, _ = detect_intent_from_message(domain, message)
        intent = normalize_intent(intent, domain)

        if intent == "general":
            intent, confidence = self._fallback_intent(message, domain)

        reply = self._build_reply(domain, intent, business, pricing_hint, message)
        result = AICompletionResult(
            text=reply,
            intent=intent,
            confidence=confidence,
            tokens_used=len(system_prompt.split()) + len(user_prompt.split()) + len(reply.split()),
            cost_estimate=0.0,
            metadata={
                "provider": "mock",
                "domain": domain,
                "model": get_model_name("mock"),
                "fallback_used": False,
            },
        )
        result.metadata["structured_output"] = build_mock_structured(result, domain=domain)
        return result

    def _fallback_intent(self, message: str, domain: str) -> tuple[str, float]:
        """Secondary keyword pass for edge cases."""
        text_lower = message.lower()
        if "@" in message or re.search(r"\+?\d{7,}", message):
            return "contact_shared", 0.88
        if any(w in text_lower for w in ("budget", "$", "usd", "dollar", "pkr", "sar")):
            return "budget_shared", 0.85
        if any(w in text_lower for w in ("week", "month", "asap", "soon")):
            return "timeline_shared", 0.84
        if any(w in text_lower for w in ("hello", "hi", "hey")):
            return "greeting", 0.80
        return "general", 0.75

    def _build_reply(
        self,
        domain: str,
        intent: str,
        business: str,
        pricing_hint: str,
        message: str,
    ) -> str:
        styles = DOMAIN_REPLY_STYLES.get(domain, DOMAIN_REPLY_STYLES["sales"])
        template = styles.get(intent) or styles.get("default", DOMAIN_REPLY_STYLES["sales"]["default"])

        pricing_text = ""
        if pricing_hint and intent == "pricing_inquiry":
            pricing_text = f"{pricing_hint} "

        reply = template.format(business=business, pricing_hint=pricing_text)

        handoff_intents = {
            "complaint", "handoff_request", "ready_to_buy", "sensitive_topic",
            "urgent_repair", "refund_request", "pricing_scope", "tax_question",
            "parent_complaint", "salary_expectation",
        }
        if intent in handoff_intents and "team member" not in reply.lower() and "connect" not in reply.lower():
            reply += " I'll connect you with a team member for final confirmation."

        return reply

    def _extract_customer_message(self, user_prompt: str) -> str:
        marker = "Customer message:"
        if marker in user_prompt:
            return user_prompt.split(marker, 1)[1].strip()
        return user_prompt.strip()

    def _extract_business_name(self, system_prompt: str) -> str:
        marker = "Business:"
        for line in system_prompt.splitlines():
            if line.startswith(marker):
                return line.replace(marker, "").strip() or "our team"
        return "our team"

    def _extract_domain(self, system_prompt: str) -> str:
        for line in system_prompt.splitlines():
            if line.startswith("Domain:"):
                return line.replace("Domain:", "").strip()
            if line.startswith("Agent template:"):
                slug = line.replace("Agent template:", "").strip()
                return get_domain_for_slug(slug)
        return "sales"

    def _extract_pricing_hint(self, system_prompt: str) -> str:
        marker = "Pricing:"
        for line in system_prompt.splitlines():
            if line.startswith(marker):
                return line.replace(marker, "").strip()
        return ""
