"""AI provider settings UI views."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import render

from apps.accounts.permissions import can_manage_ai_providers
from apps.agent_engine.services.provider_settings import get_all_providers_status, get_provider_status
from apps.agent_engine.services.provider_test import run_provider_test
from apps.agents import selectors as agent_selectors


@login_required
def ai_providers_settings_view(request):
    if not request.tenant:
        raise Http404("No tenant")
    if not can_manage_ai_providers(request.user):
        return HttpResponseForbidden("You do not have permission to manage AI providers.")

    status = get_provider_status()
    providers = get_all_providers_status()
    agents = agent_selectors.list_tenant_agents(request.tenant).select_related("template")

    return render(
        request,
        "agent_engine/ai_providers.html",
        {
            "page_title": "AI Providers",
            "active_nav": "settings",
            "status": status,
            "providers": providers,
            "agents": agents,
        },
    )


@login_required
def ai_providers_test_view(request):
    if not request.tenant:
        raise Http404("No tenant")
    if not can_manage_ai_providers(request.user):
        return HttpResponseForbidden("You do not have permission to manage AI providers.")

    agents = agent_selectors.list_tenant_agents(request.tenant).select_related("template")
    providers = get_all_providers_status()
    test_result = None

    if request.method == "POST":
        from apps.accounts.rate_limit import get_rate_limit_for_scope, rate_limit_or_429

        limit, window = get_rate_limit_for_scope("provider_test")
        blocked = rate_limit_or_429(
            request,
            "provider_test",
            limit,
            window,
            tenant=request.tenant,
            user=request.user,
            json_response=False,
        )
        if blocked:
            messages.warning(request, blocked.content.decode())
            return render(
                request,
                "agent_engine/ai_providers_test.html",
                {
                    "page_title": "Test AI Provider",
                    "active_nav": "settings",
                    "agents": agents,
                    "providers": providers,
                    "test_result": None,
                    "selected_provider": request.POST.get("provider", "mock"),
                    "selected_agent_id": request.POST.get("agent_id", ""),
                    "message_text": request.POST.get("message_text", ""),
                },
            )

        provider_name = request.POST.get("provider", "mock")
        agent_id = request.POST.get("agent_id")
        message_text = request.POST.get("message_text", "").strip()

        agent = agents.filter(pk=agent_id).first() if agent_id else agents.first()
        if not agent:
            messages.error(request, "No agent instance available for testing.")
        elif not message_text:
            messages.error(request, "Please enter a test message.")
        else:
            test_result = run_provider_test(
                provider_name=provider_name,
                agent_instance=agent,
                message_text=message_text,
                user=request.user,
                request=request,
            )

    return render(
        request,
        "agent_engine/ai_providers_test.html",
        {
            "page_title": "Test AI Provider",
            "active_nav": "settings",
            "agents": agents,
            "providers": providers,
            "test_result": test_result,
            "selected_provider": request.POST.get("provider", "mock") if request.method == "POST" else "mock",
            "selected_agent_id": request.POST.get("agent_id", ""),
            "message_text": request.POST.get("message_text", "Hello, I need help with pricing.") if request.method == "POST" else "Hello, I need help with pricing.",
        },
    )
