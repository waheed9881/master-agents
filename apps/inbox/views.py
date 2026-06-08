from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render

from apps.agents.selectors import list_tenant_agents
from apps.inbox import selectors


@login_required
def inbox_list_view(request):
    if not request.tenant:
        raise Http404("No tenant")

    conversations = selectors.list_tenant_conversations(request.tenant)
    stats = selectors.get_inbox_stats(request.tenant)

    return render(
        request,
        "inbox/list.html",
        {
            "page_title": "Inbox",
            "active_nav": "inbox",
            "conversations": conversations,
            "stats": stats,
        },
    )


@login_required
def conversation_detail_view(request, conversation_id):
    if not request.tenant:
        raise Http404("No tenant")

    conversation = selectors.get_tenant_conversation(request.tenant, conversation_id)
    if not conversation:
        raise Http404("Conversation not found")

    return render(
        request,
        "inbox/detail.html",
        {
            "page_title": conversation.contact.name,
            "active_nav": "inbox",
            "conversation": conversation,
            "messages": selectors.get_conversation_messages(conversation),
        },
    )


@login_required
def webchat_demo_view(request):
    if not request.tenant:
        raise Http404("No tenant")

    agents = list_tenant_agents(request.tenant).filter(status="active")

    return render(
        request,
        "inbox/webchat_demo.html",
        {
            "page_title": "Web Chat Demo",
            "active_nav": "inbox",
            "agents": agents,
        },
    )
