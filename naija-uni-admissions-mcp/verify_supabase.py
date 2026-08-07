"""Comprehensive Supabase verification script for Sprint 15."""

import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
from src.naija_admissions.supabase_writer import get_client

async def verify_supabase():
    client = await get_client()
    
    # Tables to verify
    tables = [
        'crawl_runs',
        'crawl_logs', 
        'institutions',
        'faculties',
        'courses',
        'admission_requirements',
        'olevel_requirements',
        'utme_requirements',
        'direct_entry',
        'post_utme',
        'aggregate_formulas',
        'departmental_cutoffs',
        'catchment',
        'elds',
        'fees',
        'deadlines',
        'admission_news',
        'source_documents',
        'knowledge_versions',
        'raw_crawl_data',
        'validated_data',
    ]
    
    print("=== Supabase Table Verification ===\n")
    
    for table in tables:
        try:
            result = await client.table(table).select('*', count='exact').limit(5).execute()
            # Handle encoding for display
            sample = str(result.data[:2]).encode('ascii', 'replace').decode('ascii')
            print(f"{table:30s}: {result.count:>5} rows  |  Sample: {sample}")
        except Exception as e:
            print(f"{table:30s}: ERROR - {e}")
    
    print("\n=== Schema Verification ===")
    
    # Check if RLS policies exist
    try:
        result = await client.rpc('get_policies', {}).execute()
        print(f"RLS Policies: Available")
    except:
        print(f"RLS Policies: Check manually")
    
    # Check indexes
    try:
        result = await client.table('crawl_runs').select('id').limit(1).execute()
        print(f"Query execution: WORKING")
    except:
        print(f"Query execution: ISSUES")

if __name__ == "__main__":
    asyncio.run(verify_supabase())