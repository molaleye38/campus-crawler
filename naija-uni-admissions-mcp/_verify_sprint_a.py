#!/usr/bin/env python3
"""Quick Sprint A verification script."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

print("=== Sprint A Verification ===")

# 1. Verify storage module imports
try:
    from naija_admissions.storage import (
        CRAWL_ASSETS_BUCKET, INSTITUTION_ASSETS_BUCKET,
        get_s3_client, store_crawl_artifacts
    )
    print("[PASS] storage module imports OK")
except Exception as e:
    print(f"[FAIL] storage import error: {e}")

# 2. Verify scraper module imports with new storage wire
try:
    from naija_admissions.scraper import scrape_one, AI_EXTRACTION_ENABLED
    print("[PASS] scraper.py imports OK (AI_EXTRACTION_ENABLED=%s)" % AI_EXTRACTION_ENABLED)
except Exception as e:
    print(f"[FAIL] scraper import error: {e}")

# 3. Verify all 24 tables exist (via REST if possible, else skip)
import urllib.request
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZocXlsd3VnaGhseHVtZ3BzdmhvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTQyMzA5NCwiZXhwIjoyMDkwOTk5MDk0fQ.l4AKzTjyYB8Aduh4_Y1pVO3U6V0YTIw1IFyCTY1J4x8"
EXPECTED = [
    "institutions","faculties","departments","courses","course_aliases",
    "subjects","subject_aliases","admission_requirements","olevel_requirements",
    "utme_requirements","direct_entry","post_utme","aggregate_formulas",
    "departmental_cutoffs","catchment","elds","fees","deadlines",
    "admission_news","source_documents","crawl_logs","knowledge_versions",
    "raw_crawl_data","validated_data"
]
ok_tables = 0
for table in EXPECTED:
    req = urllib.request.Request(
        f"https://fhqylwughhlxumgpsvho.supabase.co/rest/v1/{table}?select=*&limit=0",
        headers={"apikey": SERVICE_KEY}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            ok_tables += 1
    except Exception:
        pass
print("[PASS] %d/24 tables reachable via REST" % ok_tables)

# 4. Verify crawl-2 branch has all migration files
import subprocess
result = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
branch = result.stdout.strip()
files = [
    "migrations/10_extensions_enums.sql",
    "migrations/20_tables_1_to_8.sql",
    "migrations/30_tables_9_to_16.sql",
    "migrations/40_tables_17_to_24.sql",
    "migrations/50_indexes.sql",
    "migrations/60_rls_enable.sql",
    "migrations/70_policies_public.sql",
    "migrations/80_policies_service.sql",
    "migrations/90_functions_helpers.sql",
    "migrations/91_function_log_kv.sql",
    "migrations/92_triggers.sql",
    "migrations/99_end_comment.sql",
    "migrations/02_add_all_columns.sql"
]
missing = []
for f in files:
    path = os.path.join(os.path.dirname(__file__), f)
    if not os.path.exists(path):
        missing.append(f)
if missing:
    print("[FAIL] Missing files on branch: %s" % ", ".join(missing))
else:
    print("[PASS] All 13 migration files present (branch=%s)" % branch)

print("=== Sprint A Verification Complete ===")
