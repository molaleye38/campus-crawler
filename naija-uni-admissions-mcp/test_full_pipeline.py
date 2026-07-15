"""Full pipeline test: crawl an institution and upsert to Supabase.

Usage:
    uv run python test_full_pipeline.py [--institution "University of Lagos"]
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from dotenv import load_dotenv
load_dotenv(PROJECT_DIR / ".env")

from naija_admissions.crawl4ai_client import Crawl4AIClient
from naija_admissions.scraper import scrape_one
from naija_admissions.models import InstitutionSeed, InstitutionType, OwnershipType
from naija_admissions.supabase_ops import upsert_full_institution, close_clients
from naija_admissions.utils import safe_log


async def run_pipeline(name: str = "University of Lagos", upsert: bool = True):
    """Crawl an institution and optionally upsert to Supabase."""
    print(f"=== Pipeline Test: {name} ===\n")
    
    seed = InstitutionSeed(
        name=name,
        institution_type=InstitutionType.UNIVERSITY,
        type=OwnershipType.FEDERAL,
        state="Lagos",
        city="Lagos",
        website="https://unilag.edu.ng",
        short_name="UNILAG",
        year_established=1962,
        jamb_code="0405",
    )
    
    print(f"Target: {seed.name}")
    print(f"Website: {seed.website}")
    print(f"Type: {seed.institution_type.value}\n")
    
    async with Crawl4AIClient() as client:
        print("Starting crawl...")
        institution = await scrape_one(seed, client, lambda x: None)
        
        print(f"\n[OK] Crawl completed for {institution.name}")
        print(f"  Programs: {len(institution.programs)}")
        print(f"  Faculties: {institution.faculties}")
        print(f"  Sources: {len(institution.sources)}")
        print(f"  Confidence: {institution.confidence.get('overall', 'unknown')}")
        
        if institution.admission_requirements:
            print(f"  UTME Cutoff (general): {institution.admission_requirements.utme_cutoff_general}")
            print(f"  O-Level Credits Min: {institution.admission_requirements.olevel_credits_min}")
        
        print(f"  Fee Tiers: {len(institution.fee_tiers)}")
        print(f"  Catchment Areas: {len(institution.catchment_areas)}")
        
        if not upsert:
            print("\nSkipping Supabase upsert (--no-upsert)")
            return institution
        
        print("\nUpserting to Supabase (supabase_ops.upsert_full_institution)...")
        try:
            inst_dict = institution.model_dump(mode="json")
            
            # Convert programs to dict format expected by upsert_full_institution
            programs_list = [
                {
                    "name": p.name,
                    "faculty": p.faculty,
                    "degree": p.degree,
                    "level": p.level,
                    "duration_years": p.duration_years,
                    "affiliated_university": p.affiliated_university,
                }
                for p in institution.programs
            ]
            
            # Convert admission requirements
            admission_reqs = None
            if institution.admission_requirements:
                admission_reqs = {
                    "olevel_credits_min": institution.admission_requirements.olevel_credits_min,
                    "utme_cutoff_general": institution.admission_requirements.utme_cutoff_general,
                    "direct_entry_requirements": institution.admission_requirements.direct_entry_requirements,
                }
            
            # Convert cutoffs
            cutoff_data = None
            if institution.admission_requirements and institution.admission_requirements.utme_cutoff_per_course:
                cutoff_data = [
                    {
                        "program_name": c.course,
                        "merit_cutoff": c.cutoff,
                        "catchment_cutoff": None,
                        "elds_cutoff": None,
                    }
                    for c in institution.admission_requirements.utme_cutoff_per_course
                ]
            
            # Convert catchment areas
            catchment_data = None
            if institution.catchment_areas:
                catchment_data = [
                    {
                        "name": c.name,
                        "eligible_states": None,
                        "policy": c.policy,
                        "details": c.details,
                    }
                    for c in institution.catchment_areas
                ]
            
            # Convert fee tiers
            fee_tiers = None
            if institution.fee_tiers:
                fee_tiers = [
                    f.model_dump(mode="json")
                    for f in institution.fee_tiers
                ]
            
            # Convert sources
            sources = None
            if institution.sources:
                sources = [
                    {"url": s.url}
                    for s in institution.sources
                ]
            
            results = await upsert_full_institution(
                institution=inst_dict,
                programs=programs_list,
                faculties=institution.faculties,
                admission_reqs=admission_reqs,
                cutoff_data=cutoff_data,
                catchment_data=catchment_data,
                fee_tiers=fee_tiers,
                sources=sources,
                academic_session="2025/2026",
            )
            
            print(f"\n[OK] Upsert completed!")
            print(f"  Institution ID: {results.get('institution_id')}")
            print(f"  Faculty IDs: {len(results.get('faculty_ids', {}))} faculties")
            print(f"  Program IDs: {len(results.get('program_ids', {}))} programs")
            print(f"  Cutoff IDs: {len(results.get('cutoff_ids', []))} cutoffs")
            print(f"  Fee IDs: {len(results.get('fee_ids', []))} fees")
            print(f"  Source IDs: {len(results.get('source_ids', []))} sources")
            
            return institution, results
            
        except Exception as e:
            print(f"\n[FAIL] Upsert error: {e}")
            import traceback
            traceback.print_exc()
            return institution


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--institution", default="University of Lagos", help="Institution name")
    parser.add_argument("--no-upsert", action="store_true", help="Skip Supabase upsert")
    args = parser.parse_args()
    
    try:
        asyncio.run(run_pipeline(name=args.institution, upsert=not args.no_upsert))
    finally:
        asyncio.run(close_clients())
