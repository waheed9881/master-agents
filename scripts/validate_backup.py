#!/usr/bin/env python
"""
Validate backup files in the backups/ folder.

Usage:
    python scripts/validate_backup.py
    python scripts/validate_backup.py --file backups/backup_20260101_120000.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKUP_DIR = ROOT / "backups"


def validate_file(path: Path) -> tuple[str, str]:
    if not path.exists():
        return "FAIL", "file not found"
    size = path.stat().st_size
    if size == 0:
        return "FAIL", "file is empty"

    if path.suffix == ".json":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            count = len(data) if isinstance(data, list) else 0
            return "PASS", f"valid JSON fixture ({count} objects, {size} bytes)"
        except json.JSONDecodeError as exc:
            return "FAIL", f"invalid JSON: {exc}"

    if path.suffix == ".dump":
        return "PASS", f"PostgreSQL dump file ({size} bytes)"

    return "WARN", f"unknown format ({size} bytes)"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate backup files")
    parser.add_argument("--file", help="Specific backup file to validate")
    args = parser.parse_args()

    print("AI Agent OS - Backup Validation")
    print("=" * 40)

    if args.file:
        path = Path(args.file)
        if not path.is_absolute():
            path = ROOT / path
        status, detail = validate_file(path)
        print(f"[{status}] {path.name}: {detail}")
        print("=" * 40)
        print(f"Result: {status}")
        return 0 if status == "PASS" else 1

    if not BACKUP_DIR.exists():
        print("[WARN] backups/ folder does not exist")
        print("Run: python scripts/local_backup.py")
        print("=" * 40)
        print("Result: WARN")
        return 0

    files = sorted(BACKUP_DIR.glob("backup_*.*"), reverse=True)
    if not files:
        print("[WARN] No backup files found in backups/")
        print("Run: python scripts/local_backup.py")
        print("=" * 40)
        print("Result: WARN")
        return 0

    failures = 0
    for path in files[:10]:
        status, detail = validate_file(path)
        print(f"[{status}] {path.name}: {detail}")
        if status == "FAIL":
            failures += 1

    print("=" * 40)
    if failures:
        print(f"Result: FAIL ({failures} invalid file(s))")
        return 1
    print("Result: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
