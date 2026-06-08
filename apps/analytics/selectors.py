"""Analytics database query helpers."""
from datetime import datetime, timedelta

from django.db.models import Avg, Count, QuerySet, Sum
from django.utils import timezone

from apps.agent_engine.models import AgentRun, ToolCall, ToolCallStatus
from apps.agents.models import AgentInstance
from apps.crm.models import Lead, LeadStatus, Task
from apps.inbox.models import Conversation, Message, SenderType
from apps.integrations.models import WebhookEvent, WebhookProcessingStatus
from apps.knowledge.models import KnowledgeChunk, KnowledgeSource
from apps.tenants.models import Tenant

VALID_RANGES = ("today", "last_7_days", "last_30_days", "all_time")
DEFAULT_RANGE = "last_30_days"

FUNNEL_STATUSES = [
    LeadStatus.NEW,
    LeadStatus.QUALIFYING,
    LeadStatus.QUALIFIED,
    LeadStatus.HOT,
    LeadStatus.DEMO_BOOKED,
    LeadStatus.WON,
    LeadStatus.LOST,
]

SOURCE_BUCKETS = ("web_chat", "whatsapp", "instagram", "manual", "other")


def get_date_range(range_key: str) -> tuple[datetime | None, datetime]:
    """Return (start, end) for a range key. start is None for all_time."""
    now = timezone.now()
    if range_key == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif range_key == "last_7_days":
        start = now - timedelta(days=7)
    elif range_key == "last_30_days":
        start = now - timedelta(days=30)
    elif range_key == "all_time":
        start = None
    else:
        start = now - timedelta(days=30)
    return start, now


def _filter_range(qs: QuerySet, range_key: str, field: str = "created_at") -> QuerySet:
    start, end = get_date_range(range_key)
    if start is not None:
        qs = qs.filter(**{f"{field}__gte": start, f"{field}__lte": end})
    return qs


def normalize_lead_source(source: str) -> str:
    value = (source or "").lower().strip().replace(" ", "_")
    if value in ("web_chat", "webchat"):
        return "web_chat"
    if value == "whatsapp":
        return "whatsapp"
    if value == "instagram":
        return "instagram"
    if value in ("manual", ""):
        return "manual"
    return "other"


def leads_queryset(tenant: Tenant, range_key: str) -> QuerySet[Lead]:
    return _filter_range(Lead.objects.filter(tenant=tenant), range_key)


def conversations_queryset(tenant: Tenant, range_key: str) -> QuerySet[Conversation]:
    return _filter_range(Conversation.objects.filter(tenant=tenant), range_key)


def messages_queryset(tenant: Tenant, range_key: str) -> QuerySet[Message]:
    return _filter_range(
        Message.objects.filter(conversation__tenant=tenant),
        range_key,
    )


def agent_runs_queryset(tenant: Tenant, range_key: str) -> QuerySet[AgentRun]:
    return _filter_range(AgentRun.objects.filter(tenant=tenant), range_key)


def knowledge_sources_queryset(tenant: Tenant, range_key: str) -> QuerySet[KnowledgeSource]:
    return _filter_range(KnowledgeSource.objects.filter(tenant=tenant), range_key)


def count_leads_by_status(tenant: Tenant, range_key: str) -> dict[str, int]:
    qs = leads_queryset(tenant, range_key)
    counts = {status.value: 0 for status in FUNNEL_STATUSES}
    for row in qs.values("status").annotate(count=Count("id")):
        counts[row["status"]] = row["count"]
    return counts


def count_leads_by_source(tenant: Tenant, range_key: str) -> dict[str, int]:
    counts = {bucket: 0 for bucket in SOURCE_BUCKETS}
    for lead in leads_queryset(tenant, range_key).values_list("source", flat=True):
        bucket = normalize_lead_source(lead)
        counts[bucket] += 1
    return counts


def get_overview_counts(tenant: Tenant, range_key: str) -> dict:
    leads = leads_queryset(tenant, range_key)
    conversations = conversations_queryset(tenant, range_key)
    messages = messages_queryset(tenant, range_key)
    runs = agent_runs_queryset(tenant, range_key)
    knowledge = knowledge_sources_queryset(tenant, range_key)

    avg_score = leads.aggregate(avg=Avg("score"))["avg"] or 0

    return {
        "total_leads": leads.count(),
        "new_leads": leads.filter(status=LeadStatus.NEW).count(),
        "qualified_leads": leads.filter(status=LeadStatus.QUALIFIED).count(),
        "hot_leads": leads.filter(status=LeadStatus.HOT).count(),
        "demo_booked_leads": leads.filter(status=LeadStatus.DEMO_BOOKED).count(),
        "won_leads": leads.filter(status=LeadStatus.WON).count(),
        "lost_leads": leads.filter(status=LeadStatus.LOST).count(),
        "total_conversations": conversations.count(),
        "ai_messages_sent": messages.filter(sender_type=SenderType.AI).count(),
        "customer_messages_received": messages.filter(sender_type=SenderType.CUSTOMER).count(),
        "human_takeover_count": conversations.filter(human_takeover=True).count(),
        "total_agent_runs": runs.count(),
        "average_lead_score": round(float(avg_score), 1),
        "total_knowledge_sources": knowledge.count(),
        "agent_count": AgentInstance.objects.filter(tenant=tenant).count(),
        "webhook_events": _filter_range(WebhookEvent.objects.filter(tenant=tenant), range_key, field="received_at").count(),
        "failed_webhooks": _filter_range(
            WebhookEvent.objects.filter(tenant=tenant, processing_status=WebhookProcessingStatus.FAILED),
            range_key,
            field="received_at",
        ).count(),
    }


def get_agent_performance_rows(tenant: Tenant, range_key: str) -> list[dict]:
    agents = AgentInstance.objects.filter(tenant=tenant).select_related("template")
    rows = []
    for agent in agents:
        leads = leads_queryset(tenant, range_key).filter(agent_instance=agent)
        conversations = conversations_queryset(tenant, range_key).filter(agent_instance=agent)
        runs = agent_runs_queryset(tenant, range_key).filter(agent_instance=agent)
        avg_score = leads.aggregate(avg=Avg("score"))["avg"] or 0
        rows.append({
            "agent_id": agent.pk,
            "agent_name": agent.name,
            "template_name": agent.template.name,
            "total_conversations": conversations.count(),
            "total_leads": leads.count(),
            "hot_leads": leads.filter(status=LeadStatus.HOT).count(),
            "average_lead_score": round(float(avg_score), 1),
            "agent_runs": runs.count(),
            "human_handoffs": conversations.filter(human_takeover=True).count(),
            "knowledge_sources": KnowledgeSource.objects.filter(
                tenant=tenant, agent_instance=agent
            ).count(),
        })
    return rows


def get_inbox_counts(tenant: Tenant, range_key: str) -> dict:
    conversations = conversations_queryset(tenant, range_key)
    messages = messages_queryset(tenant, range_key)
    total_conversations = conversations.count()
    total_messages = messages.count()
    avg_messages = round(total_messages / total_conversations, 1) if total_conversations else 0

    return {
        "total_conversations": total_conversations,
        "open_conversations": conversations.filter(status="open").count(),
        "closed_conversations": conversations.filter(status="closed").count(),
        "ai_enabled_conversations": conversations.filter(ai_enabled=True).count(),
        "human_takeover_conversations": conversations.filter(human_takeover=True).count(),
        "total_messages": total_messages,
        "customer_messages": messages.filter(sender_type=SenderType.CUSTOMER).count(),
        "ai_messages": messages.filter(sender_type=SenderType.AI).count(),
        "human_messages": messages.filter(sender_type=SenderType.HUMAN).count(),
        "average_messages_per_conversation": avg_messages,
    }


def get_agent_engine_counts(tenant: Tenant, range_key: str) -> dict:
    runs = agent_runs_queryset(tenant, range_key)
    total = runs.count()
    successful = runs.exclude(output_message="").count()
    failed = total - successful
    aggregates = runs.aggregate(
        avg_confidence=Avg("confidence"),
        total_tokens=Sum("tokens_used"),
        total_cost=Sum("cost_estimate"),
    )
    runs_by_provider = {
        row["provider_name"] or "unknown": row["count"]
        for row in runs.values("provider_name").annotate(count=Count("id"))
    }
    fallback_count = runs.filter(fallback_used=True).count()
    runs_by_intent = {
        row["intent"] or "unknown": row["count"]
        for row in runs.values("intent").annotate(count=Count("id"))
    }
    latest_runs = [
        {
            "id": run.id,
            "intent": run.intent,
            "confidence": run.confidence,
            "tokens_used": run.tokens_used,
            "cost_estimate": float(run.cost_estimate),
            "provider_name": run.provider_name or "unknown",
            "model_name": run.model_name or "",
            "fallback_used": run.fallback_used,
            "created_at": run.created_at,
            "agent_name": run.agent_instance.name if run.agent_instance_id else "",
            "output_preview": (run.output_message or "")[:120],
        }
        for run in runs.select_related("agent_instance").order_by("-created_at")[:10]
    ]
    failed_tool_calls = ToolCall.objects.filter(
        agent_run__tenant=tenant,
        status=ToolCallStatus.FAILED,
    )
    failed_tool_calls = _filter_range(failed_tool_calls, range_key, field="created_at")
    if failed_tool_calls.exists():
        failed = max(failed, failed_tool_calls.values("agent_run_id").distinct().count())

    return {
        "total_runs": total,
        "successful_runs": successful,
        "failed_runs": failed,
        "average_confidence": round(float(aggregates["avg_confidence"] or 0), 2),
        "total_tokens_used": aggregates["total_tokens"] or 0,
        "estimated_cost": float(aggregates["total_cost"] or 0),
        "runs_by_intent": runs_by_intent,
        "runs_by_provider": runs_by_provider,
        "fallback_count": fallback_count,
        "latest_runs": latest_runs,
    }


def get_knowledge_counts(tenant: Tenant, range_key: str) -> dict:
    sources = knowledge_sources_queryset(tenant, range_key)
    all_sources = KnowledgeSource.objects.filter(tenant=tenant)
    chunks = KnowledgeChunk.objects.filter(tenant=tenant)
    if range_key != "all_time":
        start, end = get_date_range(range_key)
        if start:
            chunks = chunks.filter(created_at__gte=start, created_at__lte=end)

    sources_by_type = {
        row["source_type"]: row["count"]
        for row in sources.values("source_type").annotate(count=Count("id"))
    }
    top_agents = list(
        KnowledgeSource.objects.filter(tenant=tenant, agent_instance__isnull=False)
        .values("agent_instance__name", "agent_instance_id")
        .annotate(source_count=Count("id"))
        .order_by("-source_count")[:5]
    )

    return {
        "total_knowledge_sources": all_sources.count(),
        "active_sources": all_sources.count(),
        "archived_sources": 0,
        "total_chunks": chunks.count(),
        "sources_in_range": sources.count(),
        "sources_by_type": sources_by_type,
        "top_agents_by_knowledge": [
            {
                "agent_id": row["agent_instance_id"],
                "agent_name": row["agent_instance__name"],
                "source_count": row["source_count"],
            }
            for row in top_agents
        ],
    }


def get_recent_activity_rows(tenant: Tenant, range_key: str) -> dict:
    leads = [
        {
            "id": lead.id,
            "title": lead.title,
            "status": lead.status,
            "created_at": lead.created_at,
            "contact_name": lead.contact.name,
        }
        for lead in leads_queryset(tenant, range_key)
        .select_related("contact")
        .order_by("-created_at")[:5]
    ]
    conversations = [
        {
            "id": conv.id,
            "channel_type": conv.channel_type,
            "status": conv.status,
            "created_at": conv.created_at,
            "contact_name": conv.contact.name,
        }
        for conv in conversations_queryset(tenant, range_key)
        .select_related("contact")
        .order_by("-created_at")[:5]
    ]
    messages = [
        {
            "id": msg.id,
            "sender_type": msg.sender_type,
            "message_text": msg.message_text[:100],
            "created_at": msg.created_at,
            "contact_name": msg.conversation.contact.name,
        }
        for msg in messages_queryset(tenant, range_key)
        .select_related("conversation", "conversation__contact")
        .order_by("-created_at")[:5]
    ]
    runs = [
        {
            "id": run.id,
            "intent": run.intent,
            "confidence": run.confidence,
            "created_at": run.created_at,
            "agent_name": run.agent_instance.name if run.agent_instance_id else "",
        }
        for run in agent_runs_queryset(tenant, range_key)
        .select_related("agent_instance")
        .order_by("-created_at")[:5]
    ]
    tasks = list(
        _filter_range(Task.objects.filter(tenant=tenant), range_key)
        .order_by("-created_at")[:5]
        .values("id", "title", "status", "created_at")
    )
    return {
        "leads": leads,
        "conversations": conversations,
        "messages": messages,
        "agent_runs": runs,
        "tasks": tasks,
    }
