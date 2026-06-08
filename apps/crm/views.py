from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from apps.crm import selectors, services


@login_required
def leads_list_view(request):
    if not request.tenant:
        raise Http404("No tenant")

    leads = selectors.list_tenant_leads(request.tenant)
    status_filter = request.GET.get("status")
    if status_filter:
        leads = leads.filter(status=status_filter)

    stats = selectors.get_crm_stats(request.tenant)

    return render(
        request,
        "crm/leads_list.html",
        {
            "page_title": "CRM — Leads",
            "active_nav": "crm",
            "leads": leads,
            "stats": stats,
            "status_filter": status_filter,
            "status_choices": [
                ("", "All"),
                ("new", "New"),
                ("qualifying", "Qualifying"),
                ("qualified", "Qualified"),
                ("hot", "Hot"),
                ("demo_booked", "Demo Booked"),
                ("won", "Won"),
                ("lost", "Lost"),
            ],
        },
    )


@login_required
def lead_detail_view(request, lead_id):
    if not request.tenant:
        raise Http404("No tenant")

    lead = selectors.get_tenant_lead(request.tenant, lead_id)
    if not lead:
        raise Http404("Lead not found")

    return render(
        request,
        "crm/lead_detail.html",
        {
            "page_title": lead.title,
            "active_nav": "crm",
            "lead": lead,
        },
    )


@login_required
def pipeline_board_view(request):
    if not request.tenant:
        raise Http404("No tenant")

    services.ensure_default_pipeline_stages(request.tenant)
    board = selectors.get_pipeline_board(request.tenant)
    stats = selectors.get_crm_stats(request.tenant)

    return render(
        request,
        "crm/pipeline.html",
        {
            "page_title": "Pipeline",
            "active_nav": "crm",
            "board": board,
            "stats": stats,
        },
    )
