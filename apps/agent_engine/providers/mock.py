"""Deterministic mock AI provider for local demo and testing."""
import re

from apps.agent_engine.providers.base import AICompletionResult, AIProviderAdapter


class MockAIProvider(AIProviderAdapter):
    """Rule-based provider returning realistic sales assistant responses."""

    provider_name = "mock"

    def complete(self, system_prompt: str, user_prompt: str, **kwargs) -> AICompletionResult:
        message = self._extract_customer_message(user_prompt)
        text_lower = message.lower()
        business = self._extract_business_name(system_prompt)

        intent = "general"
        confidence = 0.88

        if any(w in text_lower for w in ("angry", "terrible", "worst", "refund", "complaint")):
            intent = "complaint"
            confidence = 0.92
            reply = (
                "I'm sorry to hear you're frustrated. I want to make sure you get the help you need. "
                "Let me connect you with a team member who can assist you directly."
            )
        elif any(w in text_lower for w in ("human", "person", "speak to", "talk to someone", "agent")):
            intent = "handoff_request"
            confidence = 0.95
            reply = (
                "Of course — I'll arrange for a team member to follow up with you shortly. "
                "Could you confirm the best phone number or email to reach you?"
            )
        elif any(w in text_lower for w in ("pay", "buy now", "purchase", "ready to pay", "sign up")):
            intent = "ready_to_buy"
            confidence = 0.93
            reply = (
                "That's great to hear! I'll have our sales team send you the next steps to get started. "
                "Could you confirm your preferred contact method?"
            )
        elif any(w in text_lower for w in ("discount", "cheaper", "lower price")):
            intent = "discount_request"
            confidence = 0.9
            reply = (
                "I understand you're looking for the best value. Pricing and any available offers "
                "are handled by our sales team — I'll connect you with someone who can discuss options."
            )
        elif any(w in text_lower for w in ("legal", "guarantee", "medical", "financial advice")):
            intent = "sensitive_topic"
            confidence = 0.94
            reply = (
                "I'm not able to provide legal, medical, or financial guarantees. "
                "I'll connect you with a qualified team member who can address your specific questions."
            )
        elif any(w in text_lower for w in ("price", "cost", "pricing", "how much", "quote")):
            intent = "pricing_inquiry"
            pricing_context = self._extract_pricing_hint(system_prompt)
            if pricing_context:
                reply = (
                    f"Here's an overview of our pricing: {pricing_context} "
                    "Could you share your budget range so I can recommend the best fit?"
                )
            else:
                reply = (
                    "I'd be happy to help with pricing information. Our team offers tailored packages "
                    "based on your needs. What is your budget range, and what service are you interested in?"
                )
            confidence = 0.87
        elif any(w in text_lower for w in ("demo", "call", "meeting", "schedule", "visit")):
            intent = "demo_request"
            confidence = 0.91
            reply = (
                "I'd love to schedule a call or demo for you! What day and time works best, "
                "and what's the best email or phone number to confirm?"
            )
        elif any(w in text_lower for w in ("hello", "hi", "hey", "salam", "assalam", "good morning")):
            intent = "greeting"
            reply = (
                f"Hello! Welcome to {business}. I'm an AI sales assistant here to help you find "
                "the right solution. What service are you looking for today?"
            )
        elif any(w in text_lower for w in ("budget", "$", "usd", "dollar", "pkr", "sar")):
            intent = "budget_shared"
            confidence = 0.89
            reply = (
                "Thank you for sharing that. Based on your budget, I can recommend the best options. "
                "What's your timeline for getting started, and would you like to schedule a quick call?"
            )
        elif any(w in text_lower for w in ("week", "month", "asap", "urgent", "soon", "immediately")):
            intent = "timeline_shared"
            confidence = 0.86
            reply = (
                "Got it — timeline noted. To prepare the right recommendation, "
                "could you tell me what type of business you have and your approximate budget?"
            )
        elif "@" in message or re.search(r"\+?\d{7,}", message):
            intent = "contact_shared"
            confidence = 0.9
            reply = (
                "Thank you for sharing your contact details! A team member can follow up with you. "
                "Would you like to schedule a call or demo in the meantime?"
            )
        else:
            confidence = 0.75
            reply = (
                "Thanks for your message! To help you better, could you tell me:\n"
                "1) What service are you looking for?\n"
                "2) What type of business do you have?\n"
                "3) What is your budget range?\n"
                "4) What's your timeline?"
            )

        return AICompletionResult(
            text=reply,
            intent=intent,
            confidence=confidence,
            tokens_used=len(system_prompt.split()) + len(user_prompt.split()) + len(reply.split()),
            cost_estimate=0.0,
            metadata={"provider": "mock"},
        )

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

    def _extract_pricing_hint(self, system_prompt: str) -> str:
        marker = "Pricing:"
        for line in system_prompt.splitlines():
            if line.startswith(marker):
                return line.replace(marker, "").strip()
        return ""
