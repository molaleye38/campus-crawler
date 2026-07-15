"""Test script to verify Supabase integration after schema is applied."""

import asyncio
import sys
from pathlib import Path

# Add project to path
PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from naija_admissions.supabase_client import get_client, upsert_institution, upsert_program, log_crawl


async def test_supabase_integration():
    """Test basic Supabase operations."""
    print("=== Testing Supabase Integration ===\n")
    
    try:
        client = await get_client(use_service_role=True)
        print("[OK] Client created successfully")
    except Exception as e:
        print(f"[FAIL] Failed to create client: {e}")
        return False
    
    # Test 1: Upsert institution
    print("\n1. Testing institution upsert...")
    try:
        inst = await upsert_institution(
            name="Test University",
            short_name="TU",
            institution_type="university",
            ownership_type="federal",
            state="Lagos",
            city="Lagos",
            website="https://test.edu.ng",
            admission_portal="https://admissions.test.edu.ng",
            year_established=2020,
        )
        if inst:
            print(f"  [OK] Created institution: {inst['name']} (id: {inst['id']})")
            institution_id = inst['id']
        else:
            print("  [FAIL] Failed to create institution")
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False
    
    # Test 2: Upsert program
    print("\n2. Testing program upsert...")
    try:
        prog = await upsert_program(
            institution_id=institution_id,
            name="Computer Science",
            degree="B.Sc",
            level="undergraduate",
            duration_years=4,
        )
        if prog:
            print(f"  [OK] Created program: {prog['name']} (id: {prog['id']})")
        else:
            print("  [FAIL] Failed to create program")
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
    
    # Test 3: Log crawl
    print("\n3. Testing crawl logging...")
    try:
        log = await log_crawl(
            institution_id=institution_id,
            institution_name="Test University",
            url="https://test.edu.ng/admissions",
            status="success",
            confidence="high",
            source_type="webpage",
            academic_session="2025/2026",
            pages_crawled=3,
            metadata={"test": True},
        )
        if log:
            print(f"  [OK] Logged crawl (id: {log['id']})")
        else:
            print("  [FAIL] Failed to log crawl")
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
    
    # Test 4: Query back
    print("\n4. Testing query...")
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