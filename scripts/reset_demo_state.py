#!/usr/bin/env python
"""Reset demo operational data safely (Windows-safe)."""
import argparse
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.tenants.demo_reset import reset_safe_demo_data
from apps.tenants.models import Tenant


def main():
    parser = argparse.ArgumentParser(description="Reset demo state safely.")
    parser.add_argument("--safe", action="store_true", help="Confirm safe reset.")
    parser.add_argument("--reseed", action="store_true", help="Re-seed demo data after reset.")
    parser.add_argument("--tenant-slug", default="demo-company")
    args = parser.parse_args()

    if not args.safe:
        print("Use --safe to confirm reset.")
        sys.exit(1)

    tenant = Tenant.objects.filter(slug=args.tenant_slug).first()
    if not tenant:
        print(f"Tenant not found: {args.tenant_slug}")
        sys.exit(1)

    results = reset_safe_demo_data(tenant, reseed=args.reseed)
    print(f"Reset complete for {tenant.name}")
    for key, value in results.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
