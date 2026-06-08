"""Safe demo data reset services for local development."""
from apps.agent_engine.models import AgentRun, ToolCall
from apps.crm.models import Deal, Lead, Task
from apps.inbox.models import Conversation, Message
from apps.integrations.models import WebhookEvent
from apps.tenants.models import Tenant


def reset_conversations(tenant: Tenant) -> dict[str, int]:
    msg_count = Message.objects.filter(conversation__tenant=tenant).count()
    conv_count = Conversation.objects.filter(tenant=tenant).count()
    Message.objects.filter(conversation__tenant=tenant).delete()
    Conversation.objects.filter(tenant=tenant).delete()
    return {"messages": msg_count, "conversations": conv_count}


def reset_crm_data(tenant: Tenant) -> dict[str, int]:
    task_count = Task.objects.filter(tenant=tenant).count()
    deal_count = Deal.objects.filter(tenant=tenant).count()
    lead_count = Lead.objects.filter(tenant=tenant).count()
    Task.objects.filter(tenant=tenant).delete()
    Deal.objects.filter(tenant=tenant).delete()
    Lead.objects.filter(tenant=tenant).delete()
    return {"tasks": task_count, "deals": deal_count, "leads": lead_count}


def reset_agent_runs(tenant: Tenant) -> dict[str, int]:
    run_ids = list(AgentRun.objects.filter(tenant=tenant).values_list("pk", flat=True))
    tool_count = ToolCall.objects.filter(agent_run_id__in=run_ids).count()
    run_count = len(run_ids)
    ToolCall.objects.filter(agent_run_id__in=run_ids).delete()
    AgentRun.objects.filter(tenant=tenant).delete()
    return {"tool_calls": tool_count, "agent_runs": run_count}


def reset_webhook_events(tenant: Tenant) -> dict[str, int]:
    count = WebhookEvent.objects.filter(tenant=tenant).count()
    WebhookEvent.objects.filter(tenant=tenant).delete()
    return {"webhook_events": count}


def reset_safe_demo_data(tenant: Tenant, *, reseed: bool = False) -> dict:
    """Clear demo operational data; keep tenant, users, agents, templates, knowledge."""
    results = {
        "conversations": reset_conversations(tenant),
        "crm": reset_crm_data(tenant),
        "agent_runs": reset_agent_runs(tenant),
        "webhooks": reset_webhook_events(tenant),
    }
    if reseed:
        _reseed_tenant_demo(tenant)
        results["reseeded"] = True
    return results


def _reseed_tenant_demo(tenant: Tenant) -> None:
    import importlib.util
    from pathlib import Path

    agent = tenant.agent_instances.first()
    scripts_dir = Path(__file__).resolve().parents[2] / "scripts"

    for module_name, func_name in [
        ("seed_crm_demo", "seed_crm_for_tenant"),
        ("seed_inbox_demo", "seed_inbox_for_tenant"),
    ]:
        path = scripts_dir / f"{module_name}.py"
        spec = importlib.util.spec_from_file_location(module_name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        getattr(mod, func_name)(tenant, agent_instance=agent)
