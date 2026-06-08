from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.permissions import can_manage_integrations
from apps.agents import selectors as agent_selectors
from apps.tenants.plan_limits import check_integration_limit
from apps.inbox.models import ChannelAccount
from apps.integrations.forms import ChannelAccountForm, ChannelTestForm
from apps.integrations.models import ChannelCredential, WebhookEvent
from apps.integrations.services.channel_service import (
    account_form_initial,
    create_channel_account,
    get_last_webhook_event,
    simulate_test_message,
    toggle_channel_active,
    update_channel_account,
)


def _require_tenant(request):
    if not request.tenant:
        raise Http404("No tenant")
    return request.tenant


@login_required
def integrations_index_view(request):
    tenant = _require_tenant(request)
    if not can_manage_integrations(request.user):
        return HttpResponseForbidden("You do not have permission to manage integrations.")

    accounts = ChannelAccount.objects.filter(tenant=tenant).select_related("credential")
    channel_rows = []
    for account in accounts:
        channel_rows.append({
            "account": account,
            "credential": getattr(account, "credential", None),
            "last_event": get_last_webhook_event(account),
        })

    recent_events = WebhookEvent.objects.filter(tenant=tenant).select_related(
        "conversation"
    ).order_by("-received_at")[:10]
    webhook_stats = {
        "total": WebhookEvent.objects.filter(tenant=tenant).count(),
        "failed": WebhookEvent.objects.filter(
            tenant=tenant, processing_status="failed"
        ).count(),
    }

    return render(
        request,
        "integrations/index.html",
        {
            "page_title": "Integrations",
            "active_nav": "integrations",
            "channel_rows": channel_rows,
            "recent_events": recent_events,
            "webhook_stats": webhook_stats,
            "mock_mode": getattr(settings, "INTEGRATIONS_MOCK_MODE", True),
            "webhook_urls": {
                "whatsapp": request.build_absolute_uri("/api/webhooks/whatsapp/"),
                "instagram": request.build_absolute_uri("/api/webhooks/instagram/"),
            },
        },
    )


@login_required
def channel_create_view(request):
    tenant = _require_tenant(request)
    if not can_manage_integrations(request.user):
        return HttpResponseForbidden("You do not have permission to manage integrations.")

    if request.method == "POST":
        form = ChannelAccountForm(request.POST)
        if form.is_valid():
            limit = check_integration_limit(tenant)
            if not limit.allowed:
                messages.warning(request, limit.message)
                return redirect("integrations:index")
            account = create_channel_account(tenant, form)
            messages.success(request, f"Channel '{account.display_name}' created.")
            return redirect("integrations:index")
    else:
        form = ChannelAccountForm(initial={"mock_mode": True, "is_active": True})

    return render(
        request,
        "integrations/channel_form.html",
        {
            "page_title": "New Channel",
            "active_nav": "integrations",
            "form": form,
            "is_edit": False,
        },
    )


@login_required
def channel_edit_view(request, channel_id):
    tenant = _require_tenant(request)
    account = get_object_or_404(ChannelAccount, pk=channel_id, tenant=tenant)

    if request.method == "POST":
        form = ChannelAccountForm(request.POST)
        if form.is_valid():
            update_channel_account(account, form)
            messages.success(request, f"Channel '{account.display_name}' updated.")
            return redirect("integrations:index")
    else:
        form = ChannelAccountForm(initial=account_form_initial(account))

    return render(
        request,
        "integrations/channel_form.html",
        {
            "page_title": f"Edit {account.display_name}",
            "active_nav": "integrations",
            "form": form,
            "account": account,
            "is_edit": True,
        },
    )


@login_required
def channel_toggle_view(request, channel_id):
    tenant = _require_tenant(request)
    account = get_object_or_404(ChannelAccount, pk=channel_id, tenant=tenant)
    if request.method == "POST":
        toggle_channel_active(account)
        state = "enabled" if account.is_active else "disabled"
        messages.info(request, f"Channel '{account.display_name}' {state}.")
    return redirect("integrations:index")


@login_required
def channel_test_view(request, channel_id):
    tenant = _require_tenant(request)
    account = get_object_or_404(ChannelAccount, pk=channel_id, tenant=tenant)
    agents = agent_selectors.list_tenant_agents(tenant).filter(status="active")
    test_result = None

    if request.method == "POST":
        form = ChannelTestForm(request.POST)
        if form.is_valid():
            agent = get_object_or_404(
                agents.model,
                pk=form.cleaned_data["agent_instance_id"],
                tenant=tenant,
            )
            test_result = simulate_test_message(
                tenant,
                account,
                message_text=form.cleaned_data["message_text"],
                customer_name=form.cleaned_data["customer_name"],
                customer_phone=form.cleaned_data.get("customer_phone", ""),
                customer_username=form.cleaned_data.get("customer_username", ""),
                agent_instance=agent,
            )
    else:
        default_agent = agents.first()
        form = ChannelTestForm(initial={
            "customer_name": "Test Customer",
            "agent_instance_id": default_agent.pk if default_agent else "",
            "message_text": "Hello, I need help",
        })

    return render(
        request,
        "integrations/channel_test.html",
        {
            "page_title": f"Test {account.display_name}",
            "active_nav": "integrations",
            "account": account,
            "form": form,
            "agents": agents,
            "test_result": test_result,
        },
    )


@login_required
def webhook_events_view(request):
    tenant = _require_tenant(request)
    events = WebhookEvent.objects.filter(tenant=tenant).select_related(
        "conversation"
    ).order_by("-received_at")[:100]

    return render(
        request,
        "integrations/webhook_events.html",
        {
            "page_title": "Webhook Events",
            "active_nav": "integrations",
            "events": events,
        },
    )
