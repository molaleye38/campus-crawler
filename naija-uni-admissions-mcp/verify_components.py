import os
from dotenv import load_dotenv
load_dotenv()

# Test key components
print("=== Component Verification ===")

# 1. Supabase
from src.naija_admissions.supabase_writer import get_client, upsert_crawl_run
import asyncio

async def test():
    client = await get_client()
    result = await client.table('crawl_runs').select('id,status').limit(3).execute()
    print(f'Supabase: {len(result.data)} crawl_runs')
    for r in result.data:
        print(f'  - {r["id"]}: {r["status"]}')

    # Test upsert
    test_result = await upsert_crawl_run(
        gh_run_id=999999,
        gh_run_url='https://github.com/test',
        status='success',
        inputs_json={'max_institutions': 1, 'institution_types': ['university']},
        triggered_by='test',
    )
    print(f'Upsert test: {test_result}')

asyncio.run(test())

print()
print("=== Keys verified ===")
print('NVIDIA_API_KEY:', bool(os.getenv('NVIDIA_API_KEY')))
print('SUPABASE_URL:', bool(os.getenv('SUPABASE_URL')))
print('SUPABASE_SERVICE_ROLE_KEY:', bool(os.getenv('SUPABASE_SERVICE_ROLE_KEY')))
print('AI_EXTRACTION_ENABLED:', os.getenv('AI_EXTRACTION_ENABLED'))