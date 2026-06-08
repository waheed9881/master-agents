#!/usr/bin/env python
"""
Restore a local backup (requires explicit --confirm flag).

Usage:
    python scripts/local_restore.py --file backups/backup_20260101_120000.dump --confirm
    python scripts/local_restore.py --file backups/backup_20260101_120000.json --confirm
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore AI Agent OS local backup")
    parser.add_argument("--file", required=True, help="Path to backup file")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required flag to confirm destructive restore",
    )
    args = parser.parse_args()

    backup_path = Path(args.file)
    if not backup_path.is_absolute():
        backup_path = ROOT / backup_path

    print("AI Agent OS - Local Restore")
    print("=" * 40)
    print("WARNING: This will overwrite current database data.")
    print(f"Backup file: {backup_path}")

    if not args.confirm:
        print("[FAIL] Restore aborted. Pass --confirm to proceed.")
        return 1

    if not backup_path.exists():
        print("[FAIL] Backup file not found.")
        return 1

    if backup_path.stat().st_size == 0:
        print("[FAIL] Backup file is empty.")
        return 1

    if backup_path.suffix == ".dump":
        import django

        django.setup()
        from django.conf import settings

        db = settings.DATABASES["default"]
        env = os.environ.copy()
        password = db.get("PASSWORD", "")
        if password:
            env["PGPASSWORD"] = password
        cmd = [
            "pg_restore",
            "-h", db.get("HOST") or "localhost",
            "-p", str(db.get("PORT") or "5432"),
            "-U", db.get("USER", ""),
            "-d", db.get("NAME", ""),
            "--clean",
            "--if-exists",
            str(backup_path),
        ]
        try:
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print("[PASS] PostgreSQL restore completed.")
                return 0
            print(f"[FAIL] pg_restore: {result.stderr.strip() or result.returncode}")
            return 1
        except FileNotFoundError:
            print("[FAIL] pg_restore not found. Install PostgreSQL client tools.")
            return 1

    if backup_path.suffix == ".json":
        import django

        django.setup()
        from django.core.management import call_command

        call_command("flush", "--no-input")
        call_command("loaddata", str(backup_path))
        print("[PASS] JSON fixture restore completed.")
        return 0

    print("[FAIL] Unsupported backup format (use .dump or .json)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
