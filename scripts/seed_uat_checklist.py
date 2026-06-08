#!/usr/bin/env python
"""
Seed default UAT session with MVP checklist for demo tenant.

Usage:
    python scripts/seed_uat_checklist.py

Idempotent: reuses existing session titled "MVP Demo UAT".
ASCII-only, Windows-safe output.
"""
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.accounts.models import User
from apps.agent_engine.qa_status import PRODUCT_VERSION
from apps.tenants.models import Tenant
from apps.uat.default_checklist import DEFAULT_CHECKLIST_ITEMS
from apps.uat.models import UATChecklistItem, UATSession
from apps.uat.services import create_session

SESSION_TITLE = "MVP Demo UAT"
TENANT_SLUG = "demo-company"


def seed_uat_for_tenant(tenant: Tenant, created_by: User | None = None) -> UATSession:
    session = UATSession.objects.filter(tenant=tenant, title=SESSION_TITLE).first()
    if session:
        existing = session.checklist_items.count()
        expected = len(DEFAULT_CHECKLIST_ITEMS)
        if existing < expected:
            for idx, item in enumerate(DEFAULT_CHECKLIST_ITEMS):
                if session.checklist_items.filter(section=item["section"], title=item["title"]).exists():
                    continue
                UATChecklistItem.objects.create(
                    tenant=tenant,
                    session=session,
                    section=item["section"],
                    title=item["title"],
                    description=item.get("description", ""),
                    expected_result=item.get("expected_result", ""),
                    order=idx,
                )
            print(f"Updated checklist items for session: {SESSION_TITLE}")
        else:
            print(f"UAT session already exists: {SESSION_TITLE} ({existing} items)")
        return session

    session = create_session(
        tenant,
        title=SESSION_TITLE,
        demo_version=PRODUCT_VERSION,
        audience="Internal team and client demo",
        facilitator="Demo Admin",
        created_by=created_by,
        copy_default_checklist=True,
    )
    print(f"Created UAT session: {SESSION_TITLE} ({session.checklist_items.count()} items)")
    return session


def seed():
    tenant = Tenant.objects.filter(slug=TENANT_SLUG).first()
    if not tenant:
        print(f"Tenant '{TENANT_SLUG}' not found. Run seed_demo_data.py first.")
        return

    user = User.objects.filter(tenant=tenant, email="admin@example.com").first()
    seed_uat_for_tenant(tenant, created_by=user)
    print("UAT seed complete.")


if __name__ == "__main__":
    seed()
