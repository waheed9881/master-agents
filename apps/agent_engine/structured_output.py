"""Structured agent output schema and safe JSON parsing."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field

from apps.agent_engine.domain_intents import detect_intent_from_message, get_domain_for_slug
from apps.agent_engine.providers.base import AICompletionResult

STRUCTURED_OUTPUT_JSON_INSTRUCTION = """
Respond with a single JSON object only (no markdown fences) using these fields:
{
  "reply_text": "customer-facing reply",
  "intent": "detected intent label",
  "extracted_fields": {},
  "lead_score": 0,
  "lead_status": "",
  "handoff_required": false,
  "handoff_reason": "",
  "task_required": false,
  "safety_flags": [],
  "confidence": 0.85,
  "provider_notes": ""
}
"""


@dataclass
class StructuredAgentOutput:
    reply_text: str = ""
    intent: str = "general"
    extracted_fields: dict = field(default_factory=dict)
    lead_score: int = 0
    lead_status: str = ""
    handoff_required: bool = False
    handoff_reason: str = ""
    task_required: bool = False
    safety_flags: list[str] = field(default_factory=list)
    confidence: float = 0.85
    provider_notes: str = ""
    raw_text: str = ""
    parse_valid: bool = True
    parse_source: str = "structured"

    def to_dict(self) -> dict:
        return asdict(self)


def _extract_json_block(text: str) -> str | None:
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        return fence.group(1)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        return text[start : end + 1]
    return None


def parse_structured_output(
    raw_text: str,
    *,
    domain: str = "sales",
    customer_message: str = "",
    fallback_intent: str = "general",
    fallback_confidence: float = 0.75,
) -> StructuredAgentOutput:
    """Parse provider JSON safely; fall back to text + deterministic extractor."""
    json_block = _extract_json_block(raw_text or "")
    if json_block:
        try:
            data = json.loads(json_block)
            if isinstance(data, dict) and data.get("reply_text"):
                return StructuredAgentOutput(
                    reply_text=str(data.get("reply_text", "")),
                    intent=str(data.get("intent") or fallback_intent),
                    extracted_fields=dict(data.get("extracted_fields") or {}),
                    lead_score=int(data.get("lead_score") or 0),
                    lead_status=str(data.get("lead_status") or ""),
                    handoff_required=bool(data.get("handoff_required")),
                    handoff_reason=str(data.get("handoff_reason") or ""),
                    task_required=bool(data.get("task_required")),
                    safety_flags=list(data.get("safety_flags") or []),
                    confidence=float(data.get("confidence") or fallback_confidence),
                    provider_notes=str(data.get("provider_notes") or ""),
                    raw_text=raw_text,
                    parse_valid=True,
                    parse_source="json",
                )
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    intent = fallback_intent
    if customer_message:
        detected, _, _ = detect_intent_from_message(domain, customer_message)
        if detected != "general":
            intent = detected

    return StructuredAgentOutput(
        reply_text=(raw_text or "").strip(),
        intent=intent,
        confidence=fallback_confidence,
        raw_text=raw_text,
        parse_valid=False,
        parse_source="fallback_text",
        provider_notes="Structured JSON parse failed; used plain text fallback.",
    )


def structured_from_completion(
    result: AICompletionResult,
    *,
    domain: str = "sales",
    customer_message: str = "",
) -> StructuredAgentOutput:
    """Build structured output from a provider completion result."""
    if result.metadata and result.metadata.get("structured_output"):
        data = result.metadata["structured_output"]
        if isinstance(data, dict) and data.get("reply_text"):
            return StructuredAgentOutput(
                reply_text=str(data.get("reply_text", result.text)),
                intent=str(data.get("intent") or result.intent),
                extracted_fields=dict(data.get("extracted_fields") or {}),
                lead_score=int(data.get("lead_score") or 0),
                lead_status=str(data.get("lead_status") or ""),
                handoff_required=bool(data.get("handoff_required")),
                handoff_reason=str(data.get("handoff_reason") or ""),
                task_required=bool(data.get("task_required")),
                safety_flags=list(data.get("safety_flags") or []),
                confidence=float(data.get("confidence") or result.confidence),
                provider_notes=str(data.get("provider_notes") or ""),
                raw_text=result.text,
                parse_valid=True,
                parse_source="provider_metadata",
            )

    provider = (result.metadata or {}).get("provider", "mock")
    if provider == "mock" or not _looks_like_json(result.text):
        return StructuredAgentOutput(
            reply_text=result.text,
            intent=result.intent,
            confidence=result.confidence,
            raw_text=result.text,
            parse_valid=True,
            parse_source="mock",
        )

    return parse_structured_output(
        result.text,
        domain=domain,
        customer_message=customer_message,
        fallback_intent=result.intent,
        fallback_confidence=result.confidence,
    )


def build_mock_structured(result: AICompletionResult, *, domain: str) -> dict:
    """Produce structured dict for mock provider metadata."""
    return {
        "reply_text": result.text,
        "intent": result.intent,
        "extracted_fields": {},
        "lead_score": 0,
        "lead_status": "",
        "handoff_required": result.intent in {
            "complaint", "handoff_request", "ready_to_buy", "sensitive_topic",
            "urgent_repair", "refund_request", "tax_question", "pricing_scope",
        },
        "handoff_reason": "",
        "task_required": False,
        "safety_flags": [],
        "confidence": result.confidence,
        "provider_notes": f"mock domain={domain}",
    }


def _looks_like_json(text: str) -> bool:
    text = (text or "").strip()
    return text.startswith("{") or "```json" in text
