"""Onboarding wizard for new workspaces."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.accounts.decorators import require_tenant
from apps.accounts.forms import OnboardingWorkspaceForm
from apps.accounts.permissions import can_manage_workspace
from apps.agents import selectors as agent_selectors
from apps.inbox.models import ChannelAccount
from apps.knowledge.models import KnowledgeSource


ONBOARDING_STEPS = [
    {"step": 1, "title": "Workspace profile", "slug": "profile"},
    {"step": 2, "title": "Choose agent templates", "slug": "agents"},
    {"step": 3, "title": "Add business knowledge", "slug": "knowledge"},
    {"step": 4, "title": "Configure channels (mock)", "slug": "channels"},
    {"step": 5, "title": "Test first agent message", "slug": "test"},
    {"step": 6, "title": "Finish", "slug": "finish"},
]


@login_required
@require_tenant
def onboarding_view(request):
    tenant = request.tenant
    step = int(request.GET.get("step", tenant.onboarding_step or 1))
    if step < 1 or step > 6:
        step = 1

    if request.method == "POST":
        action = request.POST.get("action", "next")
        if action == "restart" and can_manage_workspace(request.user):
            tenant.onboarding_step = 1
            tenant.onboarding_completed = False
            tenant.save(update_fields=["onboarding_step", "onboarding_completed", "updated_at"])
            messages.info(request, "Onboarding restarted.")
            return redirect("accounts:onboarding")

        if step == 1 and can_manage_workspace(request.user):
            form = OnboardingWorkspaceForm(request.POST)
            if form.is_valid():
                for field, value in form.cleaned_data.items():
                    setattr(tenant, field, value)
                tenant.onboarding_step = 2
                tenant.save()
                messages.success(request, "Workspace profile saved.")
                return redirect("accounts:onboarding?step=2")
        elif action == "skip":
            tenant.onboarding_step = min(step + 1, 6)
            tenant.save(update_fields=["onboarding_step", "updated_at"])
            return redirect(f"accounts:onboarding?step={tenant.onboarding_step}")
        elif action == "next" and step < 6:
            tenant.onboarding_step = step + 1
            tenant.save(update_fields=["onboarding_step", "updated_at"])
            return redirect(f"accounts:onboarding?step={tenant.onboarding_step}")
        elif action == "finish" or step == 6:
            tenant.onboarding_step = 6
            tenant.onboarding_completed = True
            tenant.save(update_fields=["onboarding_step", "onboarding_completed", "updated_at"])
            messages.success(request, "Onboarding complete! Welcome to AI Agent OS.")
            return redirect("dashboard:index")

    form = OnboardingWorkspaceForm(
        initial={
            "name": tenant.name,
            "country": tenant.country,
            "industry": tenant.industry,
            "timezone": tenant.timezone,
            "default_currency": tenant.default_currency,
            "business_description": tenant.business_description,
        }
    )

    templates = agent_selectors.list_active_templates()
    deployed = set(
        agent_selectors.list_tenant_agents(tenant).values_list("template__slug", flat=True)
    )
    knowledge_count = KnowledgeSource.objects.filter(tenant=tenant).count()
    channel_count = ChannelAccount.objects.filter(tenant=tenant).count()
    first_agent = agent_selectors.list_tenant_agents(tenant).first()

    return render(
        request,
        "onboarding/wizard.html",
        {
            "page_title": "Onboarding",
            "active_nav": "onboarding",
            "steps": ONBOARDING_STEPS,
            "current_step": step,
            "form": form,
            "templates": templates,
            "deployed_slugs": deployed,
            "knowledge_count": knowledge_count,
            "channel_count": channel_count,
            "first_agent": first_agent,
            "onboarding_completed": tenant.onboarding_completed,
            "can_manage": can_manage_workspace(request.user),
        },
    )
