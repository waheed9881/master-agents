#!/usr/bin/env python
"""
Route audit for important UI pages.

Uses Django test client. ASCII-only output for Windows compatibility.

Usage:
    python scripts/audit_routes.py
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

PUBLIC_ROUTES = [
    ("/login/", {200}),
]

AUTH_ROUTES = [
    ("/dashboard/", {200}),
    ("/agents/", {200}),
    ("/crm/leads/", {200}),
    ("/crm/pipeline/", {200}),
    ("/inbox/", {200}),
    ("/inbox/webchat/", {200}),
    ("/knowledge/", {200}),
    ("/analytics/", {200}),
    ("/integrations/", {200}),
]

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"


def audit_route(client: Client, path: str, expected: set[int]) -> tuple[str, str]:
    response = client.get(path, HTTP_HOST=HOST)
    code = response.status_code
    if code in expected:
        return PASS, f"GET {path} -> {code}"
    if code in (301, 302) and 200 in expected:
        return WARN, f"GET {path} -> {code} (redirect, expected {sorted(expected)})"
    return FAIL, f"GET {path} -> {code} (expected {sorted(expected)})"


def get_audit_user() -> tuple:
    user = User.objects.filter(email="admin@example.com").first()
    if user:
        return user, user.tenant
    tenant = create_tenant(name="Route Audit Co")
    user = User.objects.create_user(
        email="route-audit@example.com",
        password="RouteAudit123!",
        full_name="Route Auditor",
        tenant=tenant,
        role=UserRole.OWNER,
    )
    return user, tenant


def main() -> int:
    print("AI Agent OS - Route Audit")
    print("=" * 40)

    user, tenant = get_audit_user()
    created_temp = user.email != "admin@example.com"

    if created_temp:
        print(f"[{WARN}] Demo user not found, using temporary audit user")

    anon = Client(HTTP_HOST=HOST)
    auth = Client(HTTP_HOST=HOST)
    auth.force_login(user)

    counts = {PASS: 0, WARN: 0, FAIL: 0}

    for path, expected in PUBLIC_ROUTES:
        status, detail = audit_route(anon, path, expected)
        counts[status] += 1
        print(f"[{status}] {detail}")

    for path, expected in AUTH_ROUTES:
        status, detail = audit_route(auth, path, expected)
        counts[status] += 1
        print(f"[{status}] {detail}")

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
