"""CLI entry point for the CKAP crawler — designed for GitHub Actions / cron-free invocation.

Usage:
    ck-crawl [--max N] [--types university,polytechnic,college_of_education] [--state Lagos]
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from dotenv import load_dotenv

load_dotenv(PROJECT_DIR / ".env")

from naija_admissions import budget, resume
from naija_admissions.crawl4ai_client import Crawl4AIClient
from naija_admissions.institutions import ALL_INSTITUTIONS, filter_by_state, filter_by_type
from naija_admissions.metrics import get_metrics
from naija_admissions.models import InstitutionType
from naija_admissions.scraper import scrape_one
from naija_admissions.server import _inst_to_supabase_payload
from naija_admissions.supabase_ops import close_clients, upsert_full_institution
from naija_admissions.utils import now_iso, safe_log
from naija_admissions.writers.csv_writer import write_fees_csv, write_institutions_csv, write_programs_csv
from naija_admissions.writers.json_writer import write_json
from naija_admissions.writers.sqlite_writer import _connect, write_institution
from naija_admissions.models import Institution


DATA_DIR = PROJECT_DIR / "data"
STATE_PATH = DATA_DIR / "state.json"
JSON_PATH = DATA_DIR / "institutions.json"
INSTITUTIONS_CSV = DATA_DIR / "institutions.csv"
PROGRAMS_CSV = DATA_DIR / "programs.csv"
FEES_CSV = DATA_DIR / "fees.csv"
DB_PATH = DATA_DIR / "institutions.db"
SUPABASE_ENABLED = bool(
    __import__("os").environ.get("SUPABASE_URL") and __import__("os").environ.get("SUPABASE_SERVICE_ROLE_KEY")
)


def _load_existing() -> list[Institution]:
    if not JSON_PATH.exists():
        return []
    import json
    return [Institution.model_validate(r) for r in json.loads(JSON_PATH.read_text(encoding="utf-8"))]


def _parse_types(s: str) -> list[InstitutionType]:
    if not s:
        return None
    out = []
    for t in s.split(","):
        t = t.strip()
        if t:
            try:
                out.append(InstitutionType(t))
            except ValueError:
                safe_log("invalid_type", type=t)
    return out


async def run(args: argparse.Namespace) -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    started_at = now_iso()

    state = resume.state_load(STATE_PATH)
    ok, msg = budget.preflight(STATE_PATH)
    safe_log("preflight", ok=ok, msg=msg)

    type_enums = _parse_types(args.types)
    seeds_all = filter_by_type(ALL_INSTITUTIONS, type_enums)
    if args.state:
        seeds_all = filter_by_state(seeds_all, args.state)
    pending = resume.pending_seeds(state, seeds_all, force_overwrite=args.force)
    if args.max is not None:
        pending = pending[: args.max]

    safe_log("scrape_start", total_seeds=len(seeds_all), pending_count=len(pending),
             supabase_enabled=SUPABASE_ENABLED, max=args.max)

    records = _load_existing()
    records_by_name = {r.name: r for r in records}

    run_id = resume.start_scrape_run(state)
    scraped = 0
    failed = 0
    conn = _connect(DB_PATH)
    supabase_results: list[dict] = []
    supabase_errors: list[str] = []

    async def credit_callback(n: int) -> None:
        budget.add_credits(state, n)

    try:
        async with Crawl4AIClient(on_credits_used=credit_callback) as client:
            for i, seed in enumerate(pending, 1):
                resume.set_in_progress(state, seed.name)
                resume.state_save(STATE_PATH, state)
                try:
                    safe_log("scraping", i=i, name=seed.name)
                    inst = await scrape_one(seed, client, credit_callback)
                    records_by_name[inst.name] = inst
                    records[:] = list(records_by_name.values())
                    write_json(JSON_PATH, records)
                    write_institution(conn, inst)

                    if SUPABASE_ENABLED:
                        try:
                            payload = _inst_to_supabase_payload(inst)
                            supabase_result = await upsert_full_institution(**payload, academic_session="2025/2026")
                            if supabase_result:
                                supabase_results.append(supabase_result)
                                safe_log("supabase_upsert_ok", name=seed.name,
                                         inst_id=supabase_result.get("institution_id"))
                        except Exception as e:
                            supabase_errors.append(f"{seed.name}: {e}")
                            safe_log("supabase_upsert_error", name=seed.name, error=str(e))

                    resume.mark_completed(state, seed.name, seed.institution_type.value, seed.type.value)
                    scraped += 1
                    get_metrics().inc_institution_scraped()
                    safe_log("scraped_ok", name=seed.name, i=i,
                             programs=len(inst.programs), fees=len(inst.fee_tiers),
                             confidence=inst.confidence.get("overall"))
                except Exception as e:
                    failed += 1
                    get_metrics().inc_institution_failed()
                    resume.mark_failed(state, seed.name, str(e))
                    safe_log("scraped_failed", name=seed.name, error=str(e))
                resume.state_save(STATE_PATH, state)
    finally:
        conn.commit()
        write_institutions_csv(INSTITUTIONS_CSV, records)
        write_programs_csv(PROGRAMS_CSV, records)
        write_fees_csv(FEES_CSV, records)
        conn.close()
        if SUPABASE_ENABLED:
            await close_clients()

    credits_used = budget.credits_used_this_month(state)
    resume.end_scrape_run(state, run_id, scraped, failed, False, credits_used)
    resume.state_save(STATE_PATH, state)

    m = get_metrics().to_dict()
    safe_log("scrape_done",
             scraped=scraped, failed=failed, supabase_upserts=len(supabase_results),
             supabase_errors=len(supabase_errors), **m)

    if failed == 0 and not supabase_errors:
        return 0
    if scraped > 0:
        return 1
    return 2


def main() -> int:
    p = argparse.ArgumentParser(description="CKAP crawler CLI (GitHub Actions / manual trigger)")
    p.add_argument("--max", type=int, default=None, help="Max institutions to crawl")
    p.add_argument("--types", type=str, default="university,polytechnic,college_of_education",
                   help="Comma-separated institution types")
    p.add_argument("--state", type=str, default=None, help="Filter by state name (e.g. Lagos)")
    p.add_argument("--force", action="store_true", help="Re-crawl even if already complete")
    args = p.parse_args()
    return asyncio.run(run(args))


if __name__ == "__main__":
    sys.exit(main())
