from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from apps.agents import selectors, services
from apps.agents.models import AgentTemplate


@login_required
def agent_gallery_view(request):
    """Display all 10 agent template cards."""
    templates = selectors.list_active_templates()
    deployed_slugs = set()
    if request.tenant:
        deployed_slugs = set(
            selectors.list_tenant_agents(request.tenant).values_list(
                "template__slug", flat=True
            )
        )
    return render(
        request,
        "agents/gallery.html",
        {
            "page_title": "AI Agents",
            "active_nav": "agents",
            "templates": templates,
            "deployed_slugs": deployed_slugs,
        },
    )


@login_required
def agent_template_detail_view(request, slug):
    """Agent template detail page with deploy CTA."""
    template = selectors.get_template_by_slug(slug)
    if not template:
        raise Http404("Agent template not found")

    existing_instance = None
    if request.tenant:
        existing_instance = (
            selectors.list_tenant_agents(request.tenant)
            .filter(template=template)
            .first()
        )

    return render(
        request,
        "agents/detail.html",
        {
            "page_title": template.name,
            "active_nav": "agents",
            "template": template,
            "existing_instance": existing_instance,
        },
    )


@login_required
def deploy_agent_view(request, slug):
    """Deploy an agent instance from a template."""
    if request.method != "POST":
        return redirect("agents:detail", slug=slug)

    if not request.tenant:
        messages.error(request, "No workspace assigned to your account.")
        return redirect("agents:detail", slug=slug)

    template = get_object_or_404(AgentTemplate, slug=slug, is_active=True)
    if not template.is_implemented:
        messages.warning(request, f"{template.name} is coming soon.")
        return redirect("agents:detail", slug=slug)

    if selectors.tenant_has_agent_for_template(request.tenant, template):
        messages.info(request, f"You already have a {template.name} deployed.")
        instance = (
            selectors.list_tenant_agents(request.tenant).filter(template=template).first()
        )
        return redirect("agents:instance_detail", agent_id=instance.pk)

    instance = services.create_agent_instance(
        tenant=request.tenant,
        template=template,
    )
    messages.success(request, f"{template.name} deployed successfully!")
    return redirect("agents:instance_detail", agent_id=instance.pk)


@login_required
def agent_instance_detail_view(request, agent_id):
    """View a deployed agent instance."""
    if not request.tenant:
        raise Http404("No tenant")

    instance = selectors.get_tenant_agent(request.tenant, agent_id)
    if not instance:
        raise Http404("Agent not found")

    return render(
        request,
        "agents/instance_detail.html",
        {
            "page_title": instance.name,
            "active_nav": "agents",
            "instance": instance,
        },
    )
