#!/usr/bin/env python
"""
Smoke test for key UI routes using Django test client.

Safe to run locally; does not call external APIs.

Usage:
    python scripts/smoke_test.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.contrib.auth import get_user_model
from django.test import Client

from apps.accounts.models import UserRole
from apps.tenants.services import create_tenant

User = get_user_model()

ROUTES = [
    "/login/",
    "/dashboard/",
    "/agents/",
    "/crm/leads/",
    "/inbox/",
    "/knowledge/",
    "/analytics/",
    "/integrations/",
]


def main() -> int:
    print("AI Agent OS - Smoke Test")
    print("=" * 40)

    tenant = create_tenant(name="Smoke Test Co")
    user = User.objects.create_user(
        email="smoke@example.com",
        password="SmokeTest123!",
        full_name="Smoke Tester",
        tenant=tenant,
        role=UserRole.OWNER,
    )

    host = "localhost"
    client = Client(HTTP_HOST=host)
    client.force_login(user)

    passed = 0
    failed = 0

    for path in ROUTES:
        response = client.get(path, HTTP_HOST=host)
        if response.status_code in (200, 302):
            print(f"[PASS] GET {path} -> {response.status_code}")
            passed += 1
        else:
            print(f"[FAIL] GET {path} -> {response.status_code}")
            failed += 1

    print("=" * 40)
    print(f"Summary: {passed} passed, {failed} failed")

    user.delete()
    tenant.delete()

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
