#!/usr/bin/env python3
"""Migration script: KB SQLite (7 tables) → Unified Supabase Schema (22 tables).

Run this ONCE to migrate existing KB data to the new unified schema.
Idempotent: safe to re-run.
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
KB_DB_PATH = PROJECT_DIR / "data" / "institutions.db"

sys.path.insert(0, str(PROJECT_DIR / "src"))

from naija_admissions.supabase_ops import (
    migrate_kb_to_unified,
    get_client,
    close_clients,
)


async def main() -> None:
    print("=== CKAP Migration: KB SQLite → Unified Supabase Schema ===")
    print(f"Source DB: {KB_DB_PATH}")
    print(f"Time: {datetime.utcnow().isoformat()}")
    print()
    
    if not KB_DB_PATH.exists():
        print(f"ERROR: KB database not found at {KB_DB_PATH}")
        sys.exit(1)
    
    try:
        stats = await migrate_kb_to_unified(str(KB_DB_PATH))
        
        print("\n=== Migration Complete ===")
        for table, count in stats.items():
            print(f"  {table}: {count} rows migrated")
        
        print("\nVerifying migration...")
        client = await get_client(use_service_role=True)
        
        # Quick verification
        for table in ("institutions", "courses", "faculties", "departments", 
                      "admission_requirements", "departmental_cutoffs", "catchment", 
                      "source_documents", "fees", "deadlines", "subjects", 
                      "olevel_requirements", "utme_requirements", "direct_entry",
                      "post_utme", "aggregate_formulas", "course_aliases",
                      "subject_aliases", "elds"):
            try:
                result = await client.table(table).select("id", count="exact").execute()
                count = result.count or 0
                print(f"  {table}: {count} rows")
            except Exception as e:
                print(f"  {table}: ERROR - {e}")
        
        await close_clients()
        print("\nMigration successful!")
        
    except Exception as e:
        print(f"\nMIGRATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        await close_clients()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())