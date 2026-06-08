"""Run demo scenarios and evaluate agent quality."""
from dataclasses import dataclass, field
from uuid import uuid4

from apps.agent_engine.demo_scenarios import UNSAFE_REPLY_PHRASES, DemoScenario
from apps.agent_engine.services.orchestrator import AgentOrchestrator
from apps.agents.models import AgentInstance
from apps.crm.models import Lead, Task
from apps.inbox.models import ChannelType, SenderType
from apps.inbox.services import create_message, find_or_create_contact, find_or_create_conversation


@dataclass
class ScenarioCheck:
    name: str
    status: str  # pass, warn, fail
    detail: str = ""


@dataclass
class ScenarioRunResult:
    scenario: DemoScenario
    reply: str = ""
    intent: str = ""
    agent_run_id: int | None = None
    lead_id: int | None = None
    lead_status: str | None = None
    lead_score: int | None = None
    task_created: bool = False
    should_handoff: bool = False
    handoff_reason: str = ""
    extracted: dict = field(default_factory=dict)
    checks: list[ScenarioCheck] = field(default_factory=list)
    overall: str = "pass"  # pass, warn, fail

    def to_playground_dict(self) -> dict:
        return {
            "reply": self.reply,
            "intent": self.intent,
            "agent_run_id": self.agent_run_id,
            "lead_id": self.lead_id,
            "lead_status": self.lead_status,
            "lead_score": self.lead_score,
            "task_created": self.task_created,
            "should_handoff": self.should_handoff,
            "handoff_reason": self.handoff_reason,
            "extracted": self.extracted,
            "checks": [{"name": c.name, "status": c.status, "detail": c.detail} for c in self.checks],
            "overall": self.overall,
            "expected": {
                "intent": self.scenario.expected_intent,
                "acceptable_intents": list(self.scenario.acceptable_intents),
                "expect_handoff": self.scenario.expect_handoff,
                "expect_lead": self.scenario.expect_lead,
                "expect_task": self.scenario.expect_task,
                "demo_notes": self.scenario.demo_notes,
                "title": self.scenario.title,
            },
        }


def _intent_matches(scenario: DemoScenario, actual: str) -> bool:
    if actual == scenario.expected_intent:
        return True
    return actual in scenario.acceptable_intents


def _signals_match(scenario: DemoScenario, raw_signals: list) -> bool:
    if not scenario.expected_signals:
        return True
    return all(
        sig in raw_signals or any(sig in s for s in raw_signals)
        for sig in scenario.expected_signals
    )


def run_scenario(
    agent_instance: AgentInstance,
    scenario: DemoScenario,
    *,
    channel: str = "web_chat",
) -> ScenarioRunResult:
    """Execute one scenario through the agent pipeline and evaluate checks."""
    tenant = agent_instance.tenant
    channel_type = ChannelType.WEB_CHAT
    if channel == "whatsapp_mock":
        channel_type = ChannelType.WHATSAPP
    elif channel == "instagram_mock":
        channel_type = ChannelType.INSTAGRAM

    session_key = f"scenario_{scenario.id}_{uuid4().hex[:8]}"
    contact = find_or_create_contact(
        tenant,
        name=f"Scenario: {scenario.title[:40]}",
        source=channel_type,
    )
    conversation = find_or_create_conversation(
        tenant,
        contact,
        channel_type=channel_type,
        agent_instance=agent_instance,
        session_key=session_key,
    )
    create_message(
        conversation,
        sender_type=SenderType.CUSTOMER,
        message_text=scenario.customer_message,
        metadata={"provider": "scenario_runner", "scenario_id": scenario.id},
    )

    tasks_before = Task.objects.filter(tenant=tenant).count()
    orchestrated = AgentOrchestrator.run(agent_instance, conversation, scenario.customer_message)
    agent_result = orchestrated.agent_result if orchestrated else None
    agent_run_id = orchestrated.agent_run_id if orchestrated else None

    result = ScenarioRunResult(scenario=scenario)
    if not agent_result:
        result.checks.append(ScenarioCheck("reply_generated", "fail", "No agent result"))
        result.overall = "fail"
        return result

    if agent_result.reply:
        create_message(
            conversation,
            sender_type=SenderType.AI,
            message_text=agent_result.reply,
            metadata={"engine": "scenario_runner", "scenario_id": scenario.id},
        )

    result.reply = agent_result.reply
    result.intent = agent_result.intent
    result.agent_run_id = agent_run_id
    result.lead_id = agent_result.lead_id
    result.should_handoff = agent_result.should_handoff
    result.handoff_reason = agent_result.handoff_reason
    result.extracted = dict(agent_result.extracted_lead.__dict__)

    if agent_result.lead_id:
        lead = Lead.objects.filter(pk=agent_result.lead_id).first()
        if lead:
            result.lead_status = lead.status
            result.lead_score = lead.score

    tasks_after = Task.objects.filter(tenant=tenant).count()
    result.task_created = tasks_after > tasks_before

    checks: list[ScenarioCheck] = []

    checks.append(
        ScenarioCheck("reply_generated", "pass" if result.reply else "fail", "" if result.reply else "Empty reply")
    )
    checks.append(
        ScenarioCheck(
            "agent_run_created",
            "pass" if agent_run_id else "fail",
            "" if agent_run_id else "No AgentRun",
        )
    )

    if result.intent:
        if _intent_matches(scenario, result.intent):
            checks.append(ScenarioCheck("intent_matched", "pass", result.intent))
        else:
            checks.append(
                ScenarioCheck(
                    "intent_matched",
                    "warn",
                    f"Expected {scenario.expected_intent}, got {result.intent}",
                )
            )
    else:
        checks.append(ScenarioCheck("intent_matched", "fail", "Empty intent"))

    if scenario.expect_handoff == result.should_handoff:
        checks.append(ScenarioCheck("handoff_matched", "pass"))
    else:
        checks.append(
            ScenarioCheck(
                "handoff_matched",
                "fail",
                f"Expected handoff={scenario.expect_handoff}, got {result.should_handoff}",
            )
        )

    if scenario.expect_lead:
        checks.append(
            ScenarioCheck("crm_updated", "pass" if result.lead_id else "fail", "" if result.lead_id else "No lead")
        )
    else:
        checks.append(ScenarioCheck("crm_updated", "pass", "Lead not required"))

    if scenario.expect_task:
        checks.append(
            ScenarioCheck(
                "task_created",
                "pass" if result.task_created else "warn",
                "" if result.task_created else "Expected follow-up task",
            )
        )
    else:
        checks.append(ScenarioCheck("task_created", "pass", "Task not required"))

    raw_signals = result.extracted.get("raw_signals", [])
    if scenario.expected_signals:
        if _signals_match(scenario, raw_signals):
            checks.append(ScenarioCheck("signals_matched", "pass"))
        else:
            checks.append(ScenarioCheck("signals_matched", "warn", f"Got: {raw_signals}"))

    reply_lower = result.reply.lower()
    forbidden = list(scenario.safety_must_not_contain) + list(UNSAFE_REPLY_PHRASES)
    unsafe_found = [p for p in forbidden if p and p in reply_lower]
    if unsafe_found:
        checks.append(ScenarioCheck("safety_rule_followed", "fail", f"Unsafe: {unsafe_found[0]}"))
    else:
        checks.append(ScenarioCheck("safety_rule_followed", "pass"))

    result.checks = checks
    statuses = [c.status for c in checks]
    if "fail" in statuses:
        result.overall = "fail"
    elif "warn" in statuses:
        result.overall = "warn"
    else:
        result.overall = "pass"
    return result
