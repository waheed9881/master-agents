from django import forms
from django.db.models import Count
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.permissions import can_use_agent_playground
from apps.tenants.plan_limits import check_agent_limit

from apps.agent_engine.demo_scenarios import get_scenario_by_id, get_scenarios_for_slug
from apps.agent_engine.services.scenario_runner import run_scenario
from apps.agent_modules.registry import is_agent_implemented
from collections import defaultdict

from apps.agent_engine.demo_scenarios import scenario_count_by_slug
from apps.agents import selectors, services
from apps.agents.constants import AGENT_BEST_FOR
from apps.agents.models import AgentTemplate
from apps.crm.models import Lead
from apps.knowledge.models import KnowledgeSource


class AgentPlaygroundForm(forms.Form):
    channel = forms.ChoiceField(choices=[
        ("web_chat", "Web Chat"),
        ("whatsapp_mock", "WhatsApp (Mock)"),
        ("instagram_mock", "Instagram (Mock)"),
    ])
    scenario_id = forms.CharField(required=False)
    message_text = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}))
    action = forms.CharField(required=False, initial="send")


@login_required
def agent_gallery_view(request):
    """Display all 10 agent template cards grouped by category."""
    templates = list(selectors.list_active_templates())
    deployed_slugs = set()
    deployed_instances = {}
    knowledge_counts = {}
    scenario_counts = scenario_count_by_slug()

    if request.tenant:
        for instance in selectors.list_tenant_agents(request.tenant).select_related("template"):
            deployed_slugs.add(instance.template.slug)
            deployed_instances[instance.template.slug] = instance.pk
        for row in (
            KnowledgeSource.objects.filter(tenant=request.tenant)
            .values("agent_instance__template__slug")
            .annotate(count=Count("id"))
        ):
            slug = row.get("agent_instance__template__slug")
            if slug:
                knowledge_counts[slug] = row["count"]

    def _row(template):
        return {
            "template": template,
            "scenario_count": scenario_counts.get(template.slug, 0),
            "knowledge_count": knowledge_counts.get(template.slug, 0),
            "best_for": AGENT_BEST_FOR.get(template.slug, "Multi-channel customer engagement"),
            "deployed_instance_id": deployed_instances.get(template.slug),
            "is_deployed": template.slug in deployed_slugs,
        }

    grouped = defaultdict(list)
    for template in templates:
        grouped[template.category].append(_row(template))

    category_groups = sorted(grouped.items(), key=lambda item: item[0])

    return render(
        request,
        "agents/gallery.html",
        {
            "page_title": "AI Agents",
            "active_nav": "agents",
            "category_groups": category_groups,
            "deployed_slugs": deployed_slugs,
            "implemented_total": sum(1 for t in templates if t.is_implemented),
            "deployed_total": len(deployed_slugs),
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

    limit = check_agent_limit(request.tenant)
    if not limit.allowed:
        messages.warning(request, limit.message)
        return redirect("agents:detail", slug=slug)

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

    knowledge_count = KnowledgeSource.objects.filter(
        tenant=request.tenant, agent_instance=instance
    ).count()
    conversation_count = instance.conversations.count()
    lead_count = Lead.objects.filter(tenant=request.tenant, agent_instance=instance).count()
    brain_active = is_agent_implemented(instance.template.slug)

    return render(
        request,
        "agents/instance_detail.html",
        {
            "page_title": instance.name,
            "active_nav": "agents",
            "instance": instance,
            "brain_active": brain_active,
            "knowledge_count": knowledge_count,
            "conversation_count": conversation_count,
            "lead_count": lead_count,
        },
    )


@login_required
def agent_playground_view(request, agent_id):
    """Local agent testing playground with scenario presets."""
    if not request.tenant:
        raise Http404("No tenant")
    if not can_use_agent_playground(request.user):
        return HttpResponseForbidden("You do not have permission to use the playground.")

    instance = selectors.get_tenant_agent(request.tenant, agent_id)
    if not instance:
        raise Http404("Agent not found")

    scenarios = get_scenarios_for_slug(instance.template.slug)
    selected_scenario = None
    playground_result = None

    if request.method == "POST":
        form = AgentPlaygroundForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data.get("action", "send")
            if action == "send":
                from apps.accounts.rate_limit import get_rate_limit_for_scope, rate_limit_or_429

                limit, window = get_rate_limit_for_scope("playground")
                blocked = rate_limit_or_429(
                    request,
                    "playground",
                    limit,
                    window,
                    tenant=request.tenant,
                    user=request.user,
                    json_response=False,
                )
                if blocked:
                    return HttpResponseForbidden(blocked.content.decode())
            scenario_id = form.cleaned_data.get("scenario_id", "")
            channel = form.cleaned_data["channel"]

            if action == "load" and scenario_id:
                selected_scenario = get_scenario_by_id(scenario_id)
                form = AgentPlaygroundForm(initial={
                    "channel": channel,
                    "scenario_id": scenario_id,
                    "message_text": selected_scenario.customer_message if selected_scenario else "",
                })
            else:
                message_text = form.cleaned_data["message_text"]
                if scenario_id:
                    selected_scenario = get_scenario_by_id(scenario_id)
                run_result = run_scenario(
                    instance,
                    selected_scenario or _ad_hoc_scenario(instance.template.slug, message_text),
                    channel=channel,
                )
                playground_result = run_result.to_playground_dict()
                if scenario_id:
                    form = AgentPlaygroundForm(initial={
                        "channel": channel,
                        "scenario_id": scenario_id,
                        "message_text": message_text,
                    })
    else:
        default_scenario = scenarios[0] if scenarios else None
        form = AgentPlaygroundForm(initial={
            "channel": "web_chat",
            "scenario_id": default_scenario.id if default_scenario else "",
            "message_text": default_scenario.customer_message if default_scenario else "Hello, I need help",
        })
        if default_scenario:
            selected_scenario = default_scenario

    if not selected_scenario and form.initial.get("scenario_id"):
        selected_scenario = get_scenario_by_id(form.initial.get("scenario_id", ""))

    return render(
        request,
        "agents/playground.html",
        {
            "page_title": f"Playground — {instance.name}",
            "active_nav": "agents",
            "instance": instance,
            "form": form,
            "scenarios": scenarios,
            "selected_scenario": selected_scenario,
            "playground_result": playground_result,
            "brain_active": is_agent_implemented(instance.template.slug),
        },
    )


def _ad_hoc_scenario(template_slug: str, message: str):
    """Fallback scenario for free-form playground messages."""
    from apps.agent_engine.demo_scenarios import DemoScenario

    return DemoScenario(
        id="ad-hoc",
        template_slug=template_slug,
        title="Custom message",
        customer_message=message,
        expected_intent="general",
        expect_lead=True,
        demo_notes="Free-form test — no expected intent comparison.",
    )
