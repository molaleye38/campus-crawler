#!/usr/bin/env python3
"""Sprint F validation script — verifies key flows without heavy network ops."""
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

print("=== Sprint F Validation ===\n")

print("[1] Module imports...")
from naija_admissions.scraper import scrape_one, AI_EXTRACTION_ENABLED, WEBSITE_MAPPER_ENABLED
from naija_admissions.supabase_ops import (
    upsert_full_institution, get_client, close_clients,
    upsert_institution, upsert_faculty, upsert_course, upsert_admission_requirements,
    upsert_departmental_cutoff, upsert_catchment, upsert_fees, upsert_deadline,
    upsert_source_document, upsert_course_alias, upsert_subject, upsert_subject_alias,
    upsert_olevel_requirements, upsert_utme_requirements, upsert_direct_entry,
    upsert_post_utme, upsert_aggregate_formula, upsert_admission_news, log_crawl,
)
from naija_admissions.crawl4ai_client import Crawl4AIClient
from naija_admissions.eligibility import check_eligibility, StudentProfile
from naija_admissions.parsers import catchment_parser, fees_parser, programs_parser, requirements_parser
from naija_admissions.discovery import NBTEConnector, JAMBConnector, NUCConnector, NCCEConnector
from naija_admissions.extraction_models import SYSTEM_PROMPT, ExtractedKnowledge
from naija_admissions.resume import state_save, state_load, default_state
from naija_admissions.storage import store_crawl_artifacts, ensure_buckets_exist
print("    [OK] All modules import successfully")

print(f"\n[2] AI extraction flag: {AI_EXTRACTION_ENABLED}")
print(f"    Website mapper flag: {WEBSITE_MAPPER_ENABLED}")

print("\n[3] upsert_full_institution signature check...")
import inspect
sig = inspect.signature(upsert_full_institution)
params = list(sig.parameters)
required_sprint_c = ['course_aliases', 'subjects', 'olevel_requirements',
                      'utme_requirements', 'direct_entry', 'post_utme',
                      'aggregate_formula', 'admission_news']
for p in required_sprint_c:
    status = "[OK]" if p in params else "[FAIL]"
    print(f"    {status} parameter '{p}' present")

print("\n[4] ELDS_STATES single source check...")
from naija_admissions.utils import ELDS_STATES
from naija_admissions.parsers.catchment_parser import ELDS_STATES as CP_ELDS
from naija_admissions.eligibility import _ELDS_STATES as E_ELDS
match = list(ELDS_STATES) == list(CP_ELDS) and set(ELDS_STATES) == E_ELDS
print(f"    [{'OK' if match else 'FAIL'}] utils.ELDS_STATES == catchment_parser == eligibility")

print("\n[5] slugify single source check...")
from naija_admissions.utils import slugify
from naija_admissions.storage import slugify as S_SLUG
print(f"    [{'OK' if slugify is S_SLUG else 'FAIL'}] utils.slugify == storage.slugify")
try:
    from naija_admissions.supabase_ops import slugify as O_SLUG
    print("    [FAIL] supabase_ops still has its own slugify")
except ImportError:
    print("    [OK] supabase_ops no longer has duplicate slugify")

print("\n[6] Dead module check...")
import importlib
for mod in ['naija_admissions.supabase_client', 'naija_admissions.supabase_writer']:
    try:
        importlib.import_module(mod)
        print(f"    [FAIL] {mod} still importable")
    except ImportError:
        print(f"    [OK] {mod} removed")

print("\n[7] State save atomic + lock check...")
import tempfile, os
tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.json').name
try:
    state = default_state()
    state['completed']['Test Inst'] = {'institution_type': 'university', 'type': 'federal', 'completed_at': '2026-01-01'}
    state_save(tmp, state)
    loaded = state_load(tmp)
    assert loaded['completed']['Test Inst']['institution_type'] == 'university'
    print("    [OK] state_save + state_load round-trip")
    lock_file = tmp + '.lock'
    if os.path.exists(lock_file):
        os.unlink(lock_file)
finally:
    if os.path.exists(tmp):
        os.unlink(tmp)

print("\n=== Sprint F Validation Complete ===")
