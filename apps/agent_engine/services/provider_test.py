"""Run isolated AI provider tests for settings UI and API."""
from __future__ import annotations

from apps.agent_engine.domain_intents import get_domain_for_slug
from apps.agent_engine.providers.factory import get_ai_provider
from apps.agent_engine.services.prompt_builder import PromptBuilder
from apps.agent_engine.services.provider_settings import get_model_name, get_provider_status
from apps.agent_engine.services.safety_guardrails import evaluate_guardrails
from apps.agent_engine.structured_output import structured_from_completion
from apps.agents.models import AgentInstance


def run_provider_test(
    *,
    provider_name: str,
    agent_instance: AgentInstance,
    message_text: str,
    user=None,
    request=None,
) -> dict:
    """Execute a single provider test and return safe response payload."""
    domain = get_domain_for_slug(agent_instance.template.slug)
    system_prompt = PromptBuilder.build_system_prompt(agent_instance, "")
    user_prompt = f"Customer message: {message_text}"

    provider = get_ai_provider(provider_name, resilient=True)
    result = provider.complete(system_prompt, user_prompt)
    structured = structured_from_completion(result, domain=domain, customer_message=message_text)
    guardrails = evaluate_guardrails(
        message_text,
        structured.reply_text or result.text,
        domain=domain,
        intent=structured.intent,
        confidence=structured.confidence,
    )

    meta = dict(result.metadata or {})
    resolved = meta.get("provider_resolved") or meta.get("provider") or provider_name
    fallback_used = bool(meta.get("fallback_used")) or resolved != provider_name.lower()

    reply = guardrails.rewritten_reply or structured.reply_text or result.text
    status = get_provider_status(provider_name)

    from apps.tenants.audit import log_audit_event

    log_audit_event(
        action="ai_provider_test",
        tenant=agent_instance.tenant,
        user=user,
        object_type="agent_instance",
        object_id=agent_instance.pk,
        metadata={
            "provider": provider_name,
            "resolved": resolved,
            "safety_status": guardrails.status,
        },
        request=request,
    )
    if not guardrails.safe:
        log_audit_event(
            action="unsafe_guardrail_triggered",
            tenant=agent_instance.tenant,
            user=user,
            object_type="provider_test",
            object_id=agent_instance.pk,
            metadata={"flags": guardrails.flags, "reason": guardrails.reason},
            request=request,
        )

    return {
        "provider": resolved,
        "provider_requested": provider_name,
        "available": status["available"],
        "fallback_provider": status["fallback_provider"],
        "model": meta.get("model") or get_model_name(resolved),
        "reply": reply,
        "tokens_used": result.tokens_used,
        "cost_estimate": f"{float(result.cost_estimate):.4f}",
        "fallback_used": fallback_used,
        "structured_output_valid": structured.parse_valid,
        "structured_output": structured.to_dict(),
        "safety_status": guardrails.status if guardrails.safe else "flagged",
        "safety_flags": guardrails.flags,
        "intent": structured.intent,
        "confidence": structured.confidence,
    }
