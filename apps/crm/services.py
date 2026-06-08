"""CRM business logic services."""
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from apps.agents.models import AgentInstance
from apps.crm.models import (
    Contact,
    Deal,
    Lead,
    LeadStatus,
    PipelineStage,
    Task,
    TaskStatus,
)
from apps.tenants.models import Tenant

DEFAULT_PIPELINE_STAGES = [
    ("New", 0, True),
    ("Qualifying", 1, False),
    ("Qualified", 2, False),
    ("Proposal", 3, False),
    ("Negotiation", 4, False),
    ("Won", 5, False),
    ("Lost", 6, False),
]


def ensure_default_pipeline_stages(tenant: Tenant) -> list[PipelineStage]:
    """Create default pipeline stages for a tenant if none exist."""
    if PipelineStage.objects.filter(tenant=tenant).exists():
        return list(PipelineStage.objects.filter(tenant=tenant).order_by("order"))

    stages = []
    for name, order, is_default in DEFAULT_PIPELINE_STAGES:
        stage = PipelineStage.objects.create(
            tenant=tenant,
            name=name,
            order=order,
            is_default=is_default,
        )
        stages.append(stage)
    return stages


def create_contact(
    tenant: Tenant,
    *,
    name: str,
    phone: str = "",
    email: str = "",
    city: str = "",
    country: str = "",
    source: str = "",
    metadata: dict | None = None,
) -> Contact:
    return Contact.objects.create(
        tenant=tenant,
        name=name,
        phone=phone,
        email=email,
        city=city,
        country=country,
        source=source,
        metadata_json=metadata or {},
    )


def create_lead(
    tenant: Tenant,
    contact: Contact,
    *,
    title: str,
    agent_instance: AgentInstance | None = None,
    status: str = LeadStatus.NEW,
    score: int = 0,
    budget: str = "",
    need: str = "",
    timeline: str = "",
    source: str = "",
    summary: str = "",
) -> Lead:
    lead = Lead.objects.create(
        tenant=tenant,
        contact=contact,
        agent_instance=agent_instance,
        title=title,
        status=status,
        score=score,
        budget=budget,
        need=need,
        timeline=timeline,
        source=source or contact.source,
        summary=summary,
    )
    _maybe_create_deal_for_lead(tenant, lead)
    return lead


def update_lead(lead: Lead, **fields) -> Lead:
    allowed = {
        "title", "status", "score", "budget", "need", "timeline",
        "source", "summary", "next_follow_up_at", "agent_instance",
    }
    for key, value in fields.items():
        if key in allowed:
            setattr(lead, key, value)
    lead.save()
    return lead


def score_lead(lead: Lead) -> int:
    """Calculate lead score from available data. Full logic extended in Phase 5."""
    score = 0
    if lead.budget:
        score += 20
    if lead.timeline:
        score += 15
    if lead.need:
        score += 10
    if lead.contact.email:
        score += 15
    if lead.contact.phone:
        score += 15
    status_bonus = {
        LeadStatus.NEW: 0,
        LeadStatus.QUALIFYING: 10,
        LeadStatus.QUALIFIED: 25,
        LeadStatus.HOT: 40,
        LeadStatus.DEMO_BOOKED: 35,
        LeadStatus.WON: 50,
        LeadStatus.LOST: 0,
    }
    score += status_bonus.get(lead.status, 0)
    return min(score, 100)


def update_lead_score(lead: Lead) -> Lead:
    lead.score = score_lead(lead)
    lead.save(update_fields=["score", "updated_at"])
    return lead


def create_task(
    tenant: Tenant,
    *,
    title: str,
    lead: Lead | None = None,
    assigned_to=None,
    description: str = "",
    due_at=None,
    status: str = TaskStatus.OPEN,
) -> Task:
    return Task.objects.create(
        tenant=tenant,
        lead=lead,
        assigned_to=assigned_to,
        title=title,
        description=description,
        due_at=due_at,
        status=status,
    )


def create_deal(
    tenant: Tenant,
    lead: Lead,
    stage: PipelineStage,
    *,
    value: Decimal = Decimal("0"),
    currency: str = "USD",
    probability: int = 0,
) -> Deal:
    return Deal.objects.create(
        tenant=tenant,
        lead=lead,
        stage=stage,
        value=value,
        currency=currency,
        probability=probability,
    )


def _maybe_create_deal_for_lead(tenant: Tenant, lead: Lead) -> Deal | None:
    """Auto-create deal in default stage when lead is created."""
    stages = ensure_default_pipeline_stages(tenant)
    default_stage = next((s for s in stages if s.is_default), stages[0])
    if Deal.objects.filter(lead=lead).exists():
        return None
    return create_deal(tenant, lead, default_stage)


def create_follow_up_task(lead: Lead, days_ahead: int = 2) -> Task:
    """Create a follow-up task for a lead."""
    due = timezone.now() + timedelta(days=days_ahead)
    lead.next_follow_up_at = due
    lead.save(update_fields=["next_follow_up_at", "updated_at"])
    return create_task(
        tenant=lead.tenant,
        lead=lead,
        title=f"Follow up with {lead.contact.name}",
        description=f"Follow up on: {lead.title}",
        due_at=due,
    )


def find_or_update_lead_for_conversation(
    tenant: Tenant,
    contact: Contact,
    *,
    agent_instance: AgentInstance | None = None,
    conversation=None,
) -> Lead:
    """Find existing open lead for contact/agent or create new one."""
    qs = Lead.objects.filter(tenant=tenant, contact=contact).exclude(status=LeadStatus.LOST)
    if agent_instance:
        lead = qs.filter(agent_instance=agent_instance).order_by("-updated_at").first()
    else:
        lead = qs.order_by("-updated_at").first()
    if lead:
        return lead

    title = f"Inquiry from {contact.name}"
    if conversation:
        title = f"{conversation.get_channel_type_display()} — {contact.name}"

    return create_lead(
        tenant,
        contact,
        title=title,
        agent_instance=agent_instance,
        status=LeadStatus.NEW,
        source=contact.source or "web_chat",
    )


def detect_hot_lead(lead: Lead, extracted, intent: str = "") -> bool:
    """
    Hot lead if timeline within 30 days, budget available, demo/call request,
    contact info shared, or buying intent.
    """
    signals = getattr(extracted, "raw_signals", []) or []

    if getattr(extracted, "buying_intent", False):
        return True
    if intent in ("ready_to_buy", "demo_request"):
        return True
    if "demo_interest" in signals:
        return True
    if getattr(extracted, "budget", "") or "budget_shared" in signals:
        if "pricing_interest" in signals or intent == "pricing_inquiry":
            return True
    if getattr(extracted, "email", "") or getattr(extracted, "phone", ""):
        if getattr(extracted, "budget", "") or getattr(extracted, "timeline", ""):
            return True
    timeline = getattr(extracted, "timeline", "") or lead.timeline or ""
    urgent_timelines = ("week", "days", "asap", "immediate", "urgent", "1-2")
    if timeline and any(u in timeline.lower() for u in urgent_timelines):
        if lead.budget or getattr(extracted, "budget", "") or "pricing_interest" in signals:
            return True
    return lead.status == LeadStatus.HOT
