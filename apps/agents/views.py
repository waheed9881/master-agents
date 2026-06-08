from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from apps.agent_engine.services.orchestrator import AgentOrchestrator
from apps.agent_modules.registry import is_agent_implemented
from apps.agents import selectors, services
from apps.agents.models import AgentTemplate
from apps.crm.models import Lead
from apps.inbox.models import ChannelType
from apps.inbox.models import SenderType
from apps.inbox.services import create_message, find_or_create_contact, find_or_create_conversation
from apps.knowledge.models import KnowledgeSource


class AgentPlaygroundForm(forms.Form):
    channel = forms.ChoiceField(choices=[
        ("web_chat", "Web Chat"),
        ("whatsapp_mock", "WhatsApp (Mock)"),
        ("instagram_mock", "Instagram (Mock)"),
    ])
    message_text = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))


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
    """Local agent testing playground."""
    if not request.tenant:
        raise Http404("No tenant")

    instance = selectors.get_tenant_agent(request.tenant, agent_id)
    if not instance:
        raise Http404("Agent not found")

    playground_result = None

    if request.method == "POST":
        form = AgentPlaygroundForm(request.POST)
        if form.is_valid():
            channel = form.cleaned_data["channel"]
            channel_type = ChannelType.WEB_CHAT
            if channel == "whatsapp_mock":
                channel_type = ChannelType.WHATSAPP
            elif channel == "instagram_mock":
                channel_type = ChannelType.INSTAGRAM

            message_text = form.cleaned_data["message_text"]
            contact = find_or_create_contact(
                request.tenant, name="Playground User", source=channel_type
            )
            conversation = find_or_create_conversation(
                request.tenant,
                contact,
                channel_type=channel_type,
                agent_instance=instance,
                session_key=f"playground_{instance.pk}",
            )
            create_message(
                conversation,
                sender_type=SenderType.CUSTOMER,
                message_text=message_text,
                metadata={"provider": "playground", "channel": channel},
            )
            orchestrated = AgentOrchestrator.run(instance, conversation, message_text)
            agent_result = orchestrated.agent_result if orchestrated else None
            if agent_result:
                create_message(
                    conversation,
                    sender_type=SenderType.AI,
                    message_text=agent_result.reply,
                    metadata={
                        "engine": "playground",
                        "intent": agent_result.intent,
                        "agent_run_id": orchestrated.agent_run_id,
                    },
                )
            lead = Lead.objects.filter(pk=agent_result.lead_id).first() if agent_result and agent_result.lead_id else None

            playground_result = {
                "reply": agent_result.reply if agent_result else "",
                "intent": agent_result.intent if agent_result else "",
                "agent_run_id": orchestrated.agent_run_id if orchestrated else None,
                "lead_id": agent_result.lead_id if agent_result else None,
                "lead_status": lead.status if lead else None,
                "lead_score": lead.score if lead else None,
                "extracted": agent_result.extracted_lead.__dict__ if agent_result else {},
                "should_handoff": agent_result.should_handoff if agent_result else False,
                "handoff_reason": agent_result.handoff_reason if agent_result else "",
            }
    else:
        form = AgentPlaygroundForm(initial={
            "channel": "web_chat",
            "message_text": "Hello, I need help",
        })

    return render(
        request,
        "agents/playground.html",
        {
            "page_title": f"Playground — {instance.name}",
            "active_nav": "agents",
            "instance": instance,
            "form": form,
            "playground_result": playground_result,
            "brain_active": is_agent_implemented(instance.template.slug),
        },
    )
