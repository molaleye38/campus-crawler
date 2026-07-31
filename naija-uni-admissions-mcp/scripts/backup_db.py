#!/usr/bin/env python3
"""Dump critical Supabase tables to JSON for backup.

Runs weekly via .github/workflows/backup.yml.
Outputs to backups/YYYY-MM-DD/<table>.json, then commits to a backups/ branch.
"""
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from dotenv import load_dotenv

load_dotenv(PROJECT_DIR / ".env")

TABLES = [
    "institutions",
    "faculties",
    "departments",
    "courses",
    "admission_requirements",
    "departmental_cutoffs",
    "catchment",
    "fees",
    "deadlines",
    "elds",
]


async def main() -> None:
    from naija_admissions.supabase_ops import get_client, close_clients

    client = await get_client(use_service_role=True)
    backup_root = PROJECT_DIR / "backups"
    stamp = datetime.now(UTC).strftime("%Y-%m-%d")
    backup_dir = backup_root / stamp
    backup_dir.mkdir(parents=True, exist_ok=True)

    print(f"Backing up to {backup_dir}")
    for table in TABLES:
        try:
            result = await client.table(table).select("*").limit(100000).execute()
            data = result.data or []
            out = backup_dir / f"{table}.json"
            out.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
            print(f"  {table}: {len(data)} rows")
        except Exception as e:
            print(f"  {table}: ERROR {e}")

    await close_clients()
    print(f"Backup complete: {backup_dir}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
