#!/usr/bin/env python
"""
Create a timestamped local backup of the AI Agent OS database.

Tries pg_dump when PostgreSQL is accessible; falls back to JSON fixture export.
ASCII-only output for Windows compatibility.

Usage:
    python scripts/local_backup.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

BACKUP_DIR = ROOT / "backups"


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _pg_dump_backup(dest: Path) -> bool:
    import django

    django.setup()
    from django.conf import settings

    db = settings.DATABASES["default"]
    if db.get("ENGINE", "").endswith("sqlite3"):
        return False

    host = db.get("HOST") or "localhost"
    port = str(db.get("PORT") or "5432")
    name = db.get("NAME", "")
    user = db.get("USER", "")
    password = db.get("PASSWORD", "")

    env = os.environ.copy()
    if password:
        env["PGPASSWORD"] = password

    cmd = [
        "pg_dump",
        "-h", host,
        "-p", port,
        "-U", user,
        "-F", "c",
        "-f", str(dest),
        name,
    ]
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and dest.exists() and dest.stat().st_size > 0:
            print(f"[PASS] pg_dump backup: {dest}")
            return True
        print(f"[WARN] pg_dump failed: {result.stderr.strip() or result.returncode}")
    except FileNotFoundError:
        print("[WARN] pg_dump not found on PATH")
    except Exception as exc:
        print(f"[WARN] pg_dump error: {exc}")
    return False


def _fixture_backup(dest: Path) -> bool:
    import django

    django.setup()
    from django.core import serializers

    from apps.accounts.models import User
    from apps.agents.models import AgentInstance, AgentTemplate
    from apps.crm.models import Contact, Deal, Lead, Task
    from apps.inbox.models import ChannelAccount, Conversation, Message
    from apps.integrations.models import ChannelCredential, WebhookEvent
    from apps.knowledge.models import KnowledgeSource
    from apps.tenants.models import Plan, Tenant, TenantSubscription

    models = [
        Plan, Tenant, TenantSubscription, User, AgentTemplate, AgentInstance,
        Contact, Lead, Task, Deal, ChannelAccount, ChannelCredential,
        Conversation, Message, KnowledgeSource, WebhookEvent,
    ]
    objects = []
    for model in models:
        objects.extend(model.objects.all())

    data = serializers.serialize("json", objects)
    dest.write_text(data, encoding="utf-8")
    if dest.stat().st_size > 0:
        print(f"[PASS] JSON fixture backup: {dest} ({len(objects)} objects)")
        return True
    return False


def main() -> int:
    print("AI Agent OS - Local Backup")
    print("=" * 40)

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = _timestamp()
    pg_dest = BACKUP_DIR / f"backup_{ts}.dump"
    json_dest = BACKUP_DIR / f"backup_{ts}.json"

    if _pg_dump_backup(pg_dest):
        print("=" * 40)
        print("Result: PASS (PostgreSQL dump)")
        return 0

    if pg_dest.exists():
        pg_dest.unlink(missing_ok=True)

    if _fixture_backup(json_dest):
        print("=" * 40)
        print("Result: PASS (JSON fixture fallback)")
        return 0

    print("=" * 40)
    print("Result: FAIL (backup file empty or not created)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
