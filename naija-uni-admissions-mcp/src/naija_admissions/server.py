"""MCP server entry point — exposes the run_admissions_scrape tool.

Run with:
    uv run python -m naija_admissions.server

Stdio MCP server speaking Model Context Protocol (RPC 2.0 envelopes).

Pipeline (Phase 1-5):
    1. Website mapper discovers admission URLs for each institution
    2. Crawl4AI scrapes those pages via Playwright/Chromium
    3. NVIDIA Qwen AI extracts structured knowledge (regex fallback)
    4. Parsers normalize fees, programs, catchment, requirements
    5. Upserts to Supabase (production) + JSON/CSV/SQLite (local)
"""

from __future__ import annotations

import asyncio
import datetime as _dt
import json
import os
import sys
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from . import budget, resume
from .crawl4ai_client import Crawl4AIClient
from .institutions import ALL_INSTITUTIONS, filter_by_type, seed_counts
from .models import Institution, InstitutionType, ScrapeResult
from .scraper import scrape_one
from .supabase_ops import close_clients, upsert_full_institution
from .utils import now_iso, safe_log
from .writers.csv_writer import write_fees_csv, write_institutions_csv, write_programs_csv
from .writers.json_writer import write_json
from .writers.sqlite_writer import _connect, write_institution

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
STATE_PATH = DATA_DIR / "state.json"
JSON_PATH = DATA_DIR / "institutions.json"
INSTITUTIONS_CSV = DATA_DIR / "institutions.csv"
PROGRAMS_CSV = DATA_DIR / "programs.csv"
FEES_CSV = DATA_DIR / "fees.csv"
DB_PATH = DATA_DIR / "institutions.db"

SUPABASE_ENABLED = bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"))


def _load_existing_json_as_institutions() -> list[Institution]:
    if not JSON_PATH.exists():
        return []
    try:
        data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
        return [Institution(**d) for d in data]
    except Exception as e:
        safe_log("load_existing_failed", error=str(e))
        return []


def _sample_by_type(seeds: list, n: int) -> list:
    if not seeds or n <= 0:
        return seeds
    by_type: dict[InstitutionType, list] = {}
    for s in seeds:
        by_type.setdefault(s.institution_type, []).append(s)
    types = list(by_type.keys())
    per_type = max(1, n // len(types)) if types else 0
    out = []
    for t in types:
        out.extend(by_type[t][:per_type])
    if len(out) < n:
        for t in types:
            for s in by_type[t][per_type:]:
                out.append(s)
                if len(out) >= n:
                    break
            if len(out) >= n:
                break
    return out[:n]


def _inst_to_supabase_payload(inst: Institution) -> dict[str, Any]:
    """Convert an Institution model to the dict format expected by upsert_full_institution."""
    inst_dict = inst.model_dump(mode="json")
    
    programs_list = [
        {
            "name": p.name,
            "faculty": p.faculty,
            "degree": p.degree,
            "level": p.level,
            "duration_years": p.duration_years,
            "affiliated_university": p.affiliated_university,
        }
        for p in inst.programs
    ]
    
    admission_reqs = None
    if inst.admission_requirements:
        admission_reqs = {
            "olevel_credits_min": inst.admission_requirements.olevel_credits_min,
            "utme_cutoff_general": inst.admission_requirements.utme_cutoff_general,
            "direct_entry_requirements": inst.admission_requirements.direct_entry_requirements,
        }
    
    cutoff_data = None
    if inst.admission_requirements and inst.admission_requirements.utme_cutoff_per_course:
        cutoff_data = [
            {
                "program_name": c.course,
                "merit_cutoff": c.cutoff,
                "catchment_cutoff": None,
                "elds_cutoff": None,
            }
            for c in inst.admission_requirements.utme_cutoff_per_course
        ]
    
    catchment_data = None
    if inst.catchment_areas:
        catchment_data = [
            {
                "name": c.name,
                "eligible_states": [],
                "policy": c.policy.value if c.policy else None,
                "details": c.details,
            }
            for c in inst.catchment_areas
        ]
    
    fee_tiers = None
    if inst.fee_tiers:
        fee_tiers = [f.model_dump(mode="json") for f in inst.fee_tiers]
    
    sources = None
    if inst.sources:
        sources = [{"url": s.url} for s in inst.sources]
    
    return {
        "institution": inst_dict,
        "programs": programs_list,
        "faculties": inst.faculties,
        "admission_reqs": admission_reqs,
        "cutoff_data": cutoff_data,
        "catchment_data": catchment_data,
        "fee_tiers": fee_tiers,
        "sources": sources,
    }


async def _run_scrape(
    max_institutions: int | None,
    institution_types: list[str] | None,
    resume_run: bool,
    sample_by_type: bool,
    force_overwrite: bool,
    failed_institutions: list[str] | None = None,
) -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    started_at = now_iso()

    state = resume.state_load(STATE_PATH)
    ok, msg = budget.preflight(STATE_PATH)
    safe_log("preflight", ok=ok, msg=msg)

    type_enums = [InstitutionType(t) for t in institution_types] if institution_types else None
    seeds_all = filter_by_type(ALL_INSTITUTIONS, type_enums)
    pending = resume.pending_seeds(state, seeds_all, force_overwrite=force_overwrite)
    if failed_institutions:
        failed_set = {name.strip().lower() for name in failed_institutions if name.strip()}
        pending = [s for s in pending if s.name.strip().lower() in failed_set]
    if max_institutions is not None:
        pending = _sample_by_type(pending, max_institutions) if sample_by_type else pending[:max_institutions]

    safe_log("scrape_start", total_seeds=len(seeds_all), pending_count=len(pending),
             supabase_enabled=SUPABASE_ENABLED)

    records: list[Institution] = _load_existing_json_as_institutions()
    records_by_name = {r.name: r for r in records}

    run_id = resume.start_scrape_run(state)
    credits_at_start = budget.credits_used_this_month(state)
    scraped = 0
    failed = 0
    paused = False
    pause_reason = ""
    conn = _connect(DB_PATH)

    # Track Supabase upsert results
    supabase_results: list[dict[str, Any]] = []
    supabase_errors: list[str] = []

    async def credit_callback(n: int) -> None:
        budget.add_credits(state, n)

    try:
        async with Crawl4AIClient(on_credits_used=credit_callback) as client:
            for i, seed in enumerate(pending, 1):
                if budget.should_pause(state, credits_at_start):
                    paused = True
                    pause_reason = "MAX_PAGES_PER_RUN limit reached. Re-invoke to continue."
                    safe_log("quota_pause", name=seed.name)
                    break
                resume.set_in_progress(state, seed.name)
                resume.state_save(STATE_PATH, state)
                try:
                    safe_log("scraping", i=i, name=seed.name)
                    inst = await scrape_one(seed, client, credit_callback)
                    records_by_name[inst.name] = inst
                    records[:] = list(records_by_name.values())
                    write_json(JSON_PATH, records)
                    write_institution(conn, inst)

                    # Supabase upsert (Phase 1-5 integration)
                    supabase_result = None
                    if SUPABASE_ENABLED:
                        try:
                            payload = _inst_to_supabase_payload(inst)
                            supabase_result = await upsert_full_institution(**payload, academic_session="2025/2026")
                            if supabase_result:
                                supabase_results.append(supabase_result)
                                safe_log("supabase_upsert_ok", name=seed.name,
                                         inst_id=supabase_result.get("institution_id"),
                                         programs=len(supabase_result.get("program_ids", {})))
                        except Exception as e:
                            supabase_errors.append(f"{seed.name}: {e}")
                            safe_log("supabase_upsert_error", name=seed.name, error=str(e))

                    resume.mark_completed(state, seed.name, seed.institution_type.value, seed.type.value)
                    scraped += 1
                    safe_log("scraped_ok", name=seed.name, i=i,
                             cutoff=(inst.admission_requirements.utme_cutoff_general if inst.admission_requirements else None),
                             programs=len(inst.programs),
                             fees=len(inst.fee_tiers),
                             confidence=inst.confidence.get("overall"))

                except Exception as e:
                    failed += 1
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

    credits_used = budget.credits_used_this_month(state) - credits_at_start
    ended_at = now_iso()
    resume.end_scrape_run(state, run_id, scraped, failed, paused, credits_used)
    resume.state_save(STATE_PATH, state)

    skipped = max(0, len(seeds_all) - len(pending) - failed)
    next_window = (_dt.datetime.utcnow().replace(day=1) + _dt.timedelta(days=32)).replace(day=1).date().isoformat()

    start_dt = _dt.datetime.fromisoformat(started_at.replace("Z", "+00:00")) if "Z" in started_at else _dt.datetime.fromisoformat(started_at)
    end_dt = _dt.datetime.fromisoformat(ended_at.replace("Z", "+00:00")) if "Z" in ended_at else _dt.datetime.fromisoformat(ended_at)
    dur = int((end_dt - start_dt).total_seconds())

    result = ScrapeResult(
        scraped=scraped,
        failed=failed,
        skipped=skipped,
        duration_sec=dur,
        paths={
            "json": str(JSON_PATH),
            "institutions_csv": str(INSTITUTIONS_CSV),
            "programs_csv": str(PROGRAMS_CSV),
            "fees_csv": str(FEES_CSV),
            "sqlite": str(DB_PATH),
            "state": str(STATE_PATH),
        },
        remaining_quota={
            "used_this_month": budget.credits_used_this_month(state),
            "limit": budget.MONTHLY_LIMIT,
            "remaining": budget.remaining_quota(state),
            "next_window_starts_on": next_window,
        },
        paused=paused,
        errors=[pause_reason] if paused and pause_reason else [],
    )

    # Add Supabase results to the output
    output = result.model_dump(mode="json")
    if supabase_results:
        output["supabase_upserts"] = len(supabase_results)
        output["supabase_institution_ids"] = [r.get("institution_id") for r in supabase_results if r]
    if supabase_errors:
        output["supabase_errors"] = supabase_errors
    return output


_SCHEMA = {
    "name": "run_admissions_scrape",
    "description": (
        "Scrape admission data (requirements, fees, programs, cutoff marks, catchment areas, application process) "
        "for Nigerian tertiary institutions via Crawl4AI (local Playwright/Chromium, no API key required). "
        "Uses website mapper to discover targeted admission URLs, NVIDIA Qwen AI for structured extraction, "
        "regex parsers as fallback. Outputs JSON+CSV+SQLite locally and upserts to Supabase production DB. "
        "Resume support via state.json. Optional MAX_PAGES_PER_RUN env var caps a single run."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "max_institutions": {
                "type": "integer",
                "description": "Limit number of institutions scraped this invocation. Default 9 (pilot).",
                "default": 9,
            },
            "institution_types": {
                "type": "array",
                "items": {"type": "string", "enum": ["university", "polytechnic", "college_of_education"]},
                "default": ["university", "polytechnic", "college_of_education"],
            },
            "resume": {"type": "boolean", "default": True, "description": "Skip institutions already completed in state.json"},
            "sample_by_type": {"type": "boolean", "default": True, "description": "Sample evenly across institution_types when max_institutions set"},
            "force_overwrite": {"type": "boolean", "default": False, "description": "Re-scrape even if marked completed"},
        },
    },
}


async def _handle_message(msg: dict) -> dict | None:
    method = msg.get("method")
    id_ = msg.get("id")
    params = msg.get("params", {}) or {}

    if method == "initialize":
        return {
            "jsonrpc": "2.0", "id": id_, "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "naija-admissions", "version": "0.1.0"},
            }
        }
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": id_, "result": {"tools": [_SCHEMA]}}
    if method == "tools/call":
        name = params.get("name")
        if name != "run_admissions_scrape":
            return {"jsonrpc": "2.0", "id": id_, "error": {"code": -32601, "message": f"Unknown tool: {name}"}}
        args = params.get("arguments", {}) or {}
        max_inst = args.get("max_institutions", 9)
        if max_inst in ("null", "None", ""):
            max_inst = None
        try:
            result = await _run_scrape(
                max_institutions=max_inst,
                institution_types=args.get("institution_types"),
                resume_run=bool(args.get("resume", True)),
                sample_by_type=bool(args.get("sample_by_type", True)),
                force_overwrite=bool(args.get("force_overwrite", False)),
            )
        except Exception as e:
            return {"jsonrpc": "2.0", "id": id_, "error": {"code": -32000, "message": str(e)}}
        return {
            "jsonrpc": "2.0", "id": id_, "result": {
                "content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}],
                "isError": False,
            }
        }
    if method == "notifications/initialized":
        return None
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": -32601, "message": f"Unknown method: {method}"}}


async def _read_stdin_messages(stdin: asyncio.StreamReader, stdout: asyncio.StreamWriter) -> None:
    buf = b""
    while True:
        chunk = await stdin.read(4096)
        if not chunk:
            break
        buf += chunk
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            if not line.strip():
                continue
            try:
                msg = json.loads(line.decode("utf-8"))
            except json.JSONDecodeError:
                continue
            response = await _handle_message(msg)
            if response is not None:
                stdout.write((json.dumps(response) + "\n").encode("utf-8"))
                await stdout.drain()


async def _amain() -> None:
    loop = asyncio.get_event_loop()
    stdin = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(stdin)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    transport, _ = await loop.connect_write_pipe(lambda: asyncio.Protocol(), sys.stdout)
    stdout = asyncio.StreamWriter(transport, _, None, loop)
    safe_log("server_start", seed_counts=seed_counts())
    await _read_stdin_messages(stdin, stdout)


def main() -> None:
    try:
        asyncio.run(_amain())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
