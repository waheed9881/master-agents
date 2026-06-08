from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import redirect, render

from apps.accounts.permissions import can_manage_knowledge
from apps.agents.models import AgentInstance
from apps.tenants.plan_limits import check_knowledge_limit
from apps.agents.selectors import list_tenant_agents
from apps.knowledge import selectors, services
from apps.knowledge.forms import KnowledgeSourceForm
from apps.knowledge.models import KnowledgeSourceType


@login_required
def knowledge_list_view(request):
    if not request.tenant:
        raise Http404("No tenant")
    if not can_manage_knowledge(request.user):
        return HttpResponseForbidden("You do not have permission to manage knowledge.")

    agent_filter = request.GET.get("agent")
    agent_instance = None
    if agent_filter:
        agent_instance = AgentInstance.objects.filter(
            tenant=request.tenant, pk=agent_filter
        ).first()

    sources = selectors.list_tenant_knowledge_sources(
        request.tenant,
        agent_instance_id=agent_instance.pk if agent_instance else None,
    )
    stats = selectors.get_knowledge_stats(request.tenant, agent_instance=agent_instance)
    agents = list_tenant_agents(request.tenant)

    if request.method == "POST":
        form = KnowledgeSourceForm(request.POST)
        if form.is_valid():
            limit = check_knowledge_limit(request.tenant)
            if not limit.allowed:
                messages.warning(request, limit.message)
                return redirect("knowledge:list")
            data = form.cleaned_data
            agent = None
            if data.get("agent_instance_id"):
                agent = AgentInstance.objects.filter(
                    tenant=request.tenant, pk=data["agent_instance_id"]
                ).first()
            services.create_knowledge_source(
                request.tenant,
                title=data["title"],
                content=data["content"],
                source_type=data["source_type"],
                agent_instance=agent,
            )
            messages.success(request, "Knowledge source added.")
            redirect_url = "knowledge:list"
            if agent:
                return redirect(f"{redirect_url}?agent={agent.pk}")
            return redirect(redirect_url)
    else:
        initial = {}
        if agent_instance:
            initial["agent_instance_id"] = agent_instance.pk
        form = KnowledgeSourceForm(initial=initial)

    return render(
        request,
        "knowledge/list.html",
        {
            "page_title": "Knowledge Base",
            "active_nav": "knowledge",
            "sources": sources,
            "stats": stats,
            "agents": agents,
            "agent_filter": agent_filter,
            "selected_agent": agent_instance,
            "form": form,
            "source_types": KnowledgeSourceType.choices,
        },
    )


@login_required
def knowledge_source_detail_view(request, source_id):
    if not request.tenant:
        raise Http404("No tenant")

    source = selectors.get_tenant_knowledge_source(request.tenant, source_id)
    if not source:
        raise Http404("Knowledge source not found")

    return render(
        request,
        "knowledge/source_detail.html",
        {
            "page_title": source.title,
            "active_nav": "knowledge",
            "source": source,
            "chunks": source.chunks.all(),
        },
    )
