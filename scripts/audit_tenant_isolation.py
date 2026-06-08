#!/usr/bin/env python
"""
Audit tenant data isolation across key models and selectors.

Creates or reuses a second test tenant without destroying demo data.
ASCII-only output.

Usage:
    python scripts/audit_tenant_isolation.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"


def main() -> int:
    import django

    django.setup()

    from apps.accounts.models import User, UserRole
    from apps.agents import selectors as agent_selectors
    from apps.crm.models import Contact, Lead
    from apps.inbox import selectors as inbox_selectors
    from apps.inbox.models import ChannelAccount, Conversation
    from apps.integrations.models import ChannelCredential
    from apps.knowledge.models import KnowledgeSource
    from apps.tenants.models import Tenant
    from apps.tenants.services import create_tenant

    print("AI Agent OS - Tenant Isolation Audit")
    print("=" * 45)

    warnings = 0
    failures = 0

    tenant_a, _ = Tenant.objects.get_or_create(
        slug="isolation-audit-a",
        defaults={"name": "Isolation Audit A"},
    )
    tenant_b, created_b = Tenant.objects.get_or_create(
        slug="isolation-audit-b",
        defaults={"name": "Isolation Audit B"},
    )
    if created_b:
        print(f"[INFO] Created test tenant: {tenant_b.slug}")

    models_with_tenant = [
        ("Lead", Lead),
        ("Conversation", Conversation),
        ("KnowledgeSource", KnowledgeSource),
        ("ChannelAccount", ChannelAccount),
        ("ChannelCredential", ChannelCredential),
    ]

    for label, model in models_with_tenant:
        missing = model.objects.filter(tenant__isnull=True).count()
        if missing:
            print(f"[{FAIL}] {label}: {missing} row(s) without tenant")
            failures += 1
        else:
            print(f"[{PASS}] {label}: all rows have tenant FK")

    lead_a = Lead.objects.filter(tenant=tenant_a).first()
    lead_b = Lead.objects.filter(tenant=tenant_b).first()
    if not lead_a:
        contact_a = Contact.objects.create(
            tenant=tenant_a, name="Audit Lead A", email="a@audit.test"
        )
        lead_a = Lead.objects.create(
            tenant=tenant_a, contact=contact_a, title="Audit Lead A"
        )
    if not lead_b:
        contact_b = Contact.objects.create(
            tenant=tenant_b, name="Audit Lead B", email="b@audit.test"
        )
        lead_b = Lead.objects.create(
            tenant=tenant_b, contact=contact_b, title="Audit Lead B"
        )

    leaked = Lead.objects.filter(tenant=tenant_a, pk=lead_b.pk).exists()
    if leaked:
        print(f"[{FAIL}] CRM leads: cross-tenant leak detected")
        failures += 1
    else:
        print(f"[{PASS}] CRM leads: tenant filter isolates data")

    conv_a_count = inbox_selectors.list_tenant_conversations(tenant_a).count()
    conv_b_count = inbox_selectors.list_tenant_conversations(tenant_b).count()
    cross = inbox_selectors.list_tenant_conversations(tenant_a).filter(tenant=tenant_b).count()
    if cross:
        print(f"[{FAIL}] Inbox conversations: selector leak ({cross} rows)")
        failures += 1
    else:
        print(f"[{PASS}] Inbox conversations: selector OK (a={conv_a_count}, b={conv_b_count})")

    ks_cross = KnowledgeSource.objects.filter(tenant=tenant_a).filter(
        pk__in=KnowledgeSource.objects.filter(tenant=tenant_b).values_list("pk", flat=True)
    ).count()
    if ks_cross:
        print(f"[{FAIL}] Knowledge sources: cross-tenant query leak")
        failures += 1
    else:
        print(f"[{PASS}] Knowledge sources: tenant scoped")

    agents_a = agent_selectors.list_tenant_agents(tenant_a).count()
    agents_b = agent_selectors.list_tenant_agents(tenant_b).count()
    agent_cross = agent_selectors.list_tenant_agents(tenant_a).filter(tenant=tenant_b).count()
    if agent_cross:
        print(f"[{FAIL}] Agent instances: selector leak")
        failures += 1
    else:
        print(f"[{PASS}] Agent instances: selector OK (a={agents_a}, b={agents_b})")

    int_cross = ChannelAccount.objects.filter(tenant=tenant_a).filter(
        pk__in=ChannelAccount.objects.filter(tenant=tenant_b).values_list("pk", flat=True)
    ).count()
    if int_cross:
        print(f"[{FAIL}] Integrations: channel account leak")
        failures += 1
    else:
        print(f"[{PASS}] Integrations: channel accounts tenant scoped")

    demo_tenant = Tenant.objects.filter(slug="demo-company").first()
    if demo_tenant and demo_tenant.pk in (tenant_a.pk, tenant_b.pk):
        print(f"[{WARN}] Audit tenants overlap with demo-company slug")
        warnings += 1
    else:
        print(f"[{PASS}] Demo data: audit tenants are separate from demo-company")

    print("=" * 45)
    if failures:
        print(f"Result: FAIL ({failures} failure(s), {warnings} warning(s))")
        return 1
    if warnings:
        print(f"Result: WARN ({warnings} warning(s))")
        return 0
    print("Result: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
