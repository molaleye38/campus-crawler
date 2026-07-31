"""Test script to verify Supabase integration after schema is applied.

Updated for supabase_ops (Sprint B cleanup — old supabase_client/supabase_writer removed).
"""

import asyncio
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from naija_admissions.supabase_ops import get_client, upsert_full_institution, log_crawl


async def test_supabase_integration():
    print("=== Testing Supabase Integration ===\n")

    try:
        client = await get_client(use_service_role=True)
        print("[OK] Client created successfully")
    except Exception as e:
        print(f"[FAIL] Failed to create client: {e}")
        return False

    print("\n1. Testing institution + programs upsert (upsert_full_institution)...")
    try:
        result = await upsert_full_institution(
            institution={
                "name": "Test University",
                "short_name": "TU",
                "institution_type": "university",
                "type": "federal",
                "state": "Lagos",
                "city": "Lagos",
                "website": "https://test.edu.ng",
                "admission_portal": "https://admissions.test.edu.ng",
                "year_established": 2020,
            },
            faculties=[],
            programs=[
                {
                    "name": "Computer Science",
                    "degree": "BSc",
                    "level": "undergraduate",
                    "duration_years": 4,
                }
            ],
        )
        if result:
            print(f"  [OK] Upserted institution + programs: {result.get('institution_id', '?')}")
            institution_id = result.get("institution_id")
        else:
            print("  [FAIL] Upsert returned no result")
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False

    print("\n2. Testing crawl logging...")
    try:
        log = await log_crawl(
            institution_id=institution_id,
            url="https://test.edu.ng/admissions",
            status="success",
            confidence="high",
            source_type="webpage",
            academic_session="2025/2026",
            pages_crawled=3,
            metadata={"test": True},
        )
        if log:
            print(f"  [OK] Logged crawl (id: {log.get('id', '?')})")
        else:
            print("  [FAIL] Failed to log crawl")
    except Exception as e:
        print(f"  [FAIL] Error: {e}")

    print("\n3. Testing query back...")
    try:
        result = await client.table("institutions").select("*").eq("name", "Test University").execute()
        if result.data:
            print(f"  [OK] Queried back: {result.data[0]['name']}")
        else:
            print("  [FAIL] Query returned no data")
    except Exception as e:
        print(f"  [FAIL] Query error: {e}")

    print("\n=== All tests completed ===")
    return True


if __name__ == "__main__":
    asyncio.run(test_supabase_integration())
