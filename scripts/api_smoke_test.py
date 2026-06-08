#!/usr/bin/env python
"""
API smoke test for important authenticated endpoints.

No external APIs are called. ASCII-only output.

Usage:
    python scripts/api_smoke_test.py
"""
from __future__ import annotations

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
HOST = "localhost"

API_ROUTES = [
    "/api/me/",
    "/api/agent-templates/",
    "/api/agents/",
    "/api/leads/",
    "/api/conversations/",
    "/api/knowledge/",
    "/api/analytics/overview/",
    "/api/integrations/channel-accounts/",
]

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"


def get_demo_user() -> tuple:
    user = User.objects.filter(email="admin@example.com").first()
    if user:
        return user, user.tenant, False
    tenant = create_tenant(name="API Smoke Co")
    user = User.objects.create_user(
        email="api-smoke@example.com",
        password="ApiSmoke123!",
        full_name="API Smoke Tester",
        tenant=tenant,
        role=UserRole.OWNER,
    )
    return user, tenant, True


def main() -> int:
    print("AI Agent OS - API Smoke Test")
    print("=" * 40)

    user, tenant, created_temp = get_demo_user()
    if created_temp:
        print(f"[{WARN}] Demo user admin@example.com not found, using temporary user")
        print(f"[{WARN}] Run: python scripts/seed_demo_data.py for full demo coverage")

    client = Client(HTTP_HOST=HOST)
    client.force_login(user)

    counts = {PASS: 0, WARN: 0, FAIL: 0}

    for path in API_ROUTES:
        response = client.get(path, HTTP_HOST=HOST)
        code = response.status_code
        if code == 200:
            counts[PASS] += 1
            print(f"[{PASS}] GET {path} -> {code}")
        elif code == 403:
            counts[FAIL] += 1
            print(f"[{FAIL}] GET {path} -> {code} (forbidden)")
        else:
            counts[FAIL] += 1
            print(f"[{FAIL}] GET {path} -> {code} (expected 200)")

    if created_temp:
        user.delete()
        tenant.delete()

    print("=" * 40)
    print(f"Summary: {counts[PASS]} PASS, {counts[WARN]} WARN, {counts[FAIL]} FAIL")

    if counts[FAIL] > 0:
        print("Result: FAIL")
        return 1
    if counts[WARN] > 0:
        print("Result: WARN")
        return 0
    print("Result: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
