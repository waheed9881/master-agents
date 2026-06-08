"""CRM query helpers."""
from django.db.models import Count, QuerySet

from apps.crm.models import Contact, Deal, Lead, PipelineStage, Task
from apps.tenants.models import Tenant


def list_tenant_contacts(tenant: Tenant) -> QuerySet[Contact]:
    return Contact.objects.filter(tenant=tenant)


def list_tenant_leads(tenant: Tenant) -> QuerySet[Lead]:
    return (
        Lead.objects.filter(tenant=tenant)
        .select_related("contact", "agent_instance")
        .prefetch_related("tasks", "deals")
    )


def get_tenant_lead(tenant: Tenant, lead_id: int) -> Lead | None:
    return (
        Lead.objects.filter(tenant=tenant, pk=lead_id)
        .select_related("contact", "agent_instance")
        .prefetch_related("tasks", "deals__stage")
        .first()
    )


def list_tenant_pipeline_stages(tenant: Tenant) -> QuerySet[PipelineStage]:
    return PipelineStage.objects.filter(tenant=tenant).annotate(
        deal_count=Count("deals")
    )


def get_pipeline_board(tenant: Tenant) -> list[dict]:
    """Return pipeline stages with their deals for kanban view."""
    stages = PipelineStage.objects.filter(tenant=tenant).order_by("order")
    board = []
    for stage in stages:
        deals = (
            Deal.objects.filter(tenant=tenant, stage=stage)
            .select_related("lead", "lead__contact")
            .order_by("-updated_at")
        )
        board.append({"stage": stage, "deals": deals})
    return board


def get_crm_stats(tenant: Tenant) -> dict:
    leads = Lead.objects.filter(tenant=tenant)
    return {
        "total_leads": leads.count(),
        "hot_leads": leads.filter(status="hot").count(),
        "qualified_leads": leads.filter(status="qualified").count(),
        "demo_booked": leads.filter(status="demo_booked").count(),
        "won_leads": leads.filter(status="won").count(),
        "open_tasks": Task.objects.filter(tenant=tenant, status="open").count(),
        "total_contacts": Contact.objects.filter(tenant=tenant).count(),
    }
