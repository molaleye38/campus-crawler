"""Supabase writer for Campus Compass knowledge base.

Handles upserts for all production tables, staging layer operations,
and crawl logging after each successful crawl.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
    project_root = Path(__file__).resolve().parent.parent.parent
    load_dotenv(project_root / ".env")
except ImportError:
    pass

from postgrest import APIError
from supabase._async.client import AsyncClient, create_client

_SUPABASE_URL = os.getenv("SUPABASE_URL")
_SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

_client: AsyncClient | None = None


async def get_client(use_service_role: bool = False) -> AsyncClient:
    """Get or create async Supabase client with service role for admin operations."""
    global _client

    if _client is None:
        if not _SUPABASE_URL or not _SUPABASE_SERVICE_KEY:
            raise RuntimeError(
                "Supabase not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env"
            )
        _client = await create_client(_SUPABASE_URL, _SUPABASE_SERVICE_KEY)
    return _client


async def run_with_retry(coro, max_retries: int = 3, base_delay: float = 1.0) -> Any:
    """Run async operation with exponential backoff retry."""
    last_exc = None
    for attempt in range(max_retries):
        try:
            return await coro
        except (TimeoutError, APIError) as e:
            last_exc = e
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
            continue
    raise last_exc


def _generate_content_hash(data: dict) -> str:
    """Generate SHA256 hash of normalized content for change detection."""
    normalized = {k: v for k, v in data.items() if k not in ("crawled_at", "last_updated", "id", "created_at", "updated_at")}
    serialized = json.dumps(normalized, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()[:16]


async def upsert_institution(
    name: str,
    short_name: str | None = None,
    institution_type: str = "university",
    ownership_type: str = "federal",
    state: str | None = None,
    city: str | None = None,
    website: str | None = None,
    admission_portal: str | None = None,
    year_established: int | None = None,
) -> dict | None:
    """Upsert institution. Returns the upserted row."""
    client = await get_client()

    data = {
        "name": name,
        "short_name": short_name,
        "institution_type": institution_type,
        "ownership_type": ownership_type,
        "state": state,
        "city": city,
        "website": website,
        "admission_portal": admission_portal,
        "year_established": year_established,
        "last_updated": datetime.utcnow().isoformat(),
    }
    data = {k: v for k, v in data.items() if v is not None}

    result = await run_with_retry(
        client.table("institutions").upsert(data, on_conflict="name").execute()
    )
    return result.data[0] if result.data else None


async def upsert_faculty(
    institution_id: str,
    name: str,
) -> dict | None:
    """Upsert faculty."""
    client = await get_client()
    data = {"institution_id": institution_id, "name": name}

    result = await run_with_retry(
        client.table("faculties").upsert(data, on_conflict="institution_id,name").execute()
    )
    return result.data[0] if result.data else None


async def upsert_program(
    institution_id: str,
    name: str,
    faculty_id: str | None = None,
    degree: str | None = None,
    level: str | None = None,
    duration_years: int | None = None,
    affiliated_university: str | None = None,
) -> dict | None:
    """Upsert program."""
    client = await get_client()
    data = {
        "institution_id": institution_id,
        "name": name,
        "faculty_id": faculty_id,
        "degree": degree,
        "level": level,
        "duration_years": duration_years,
        "affiliated_university": affiliated_university,
    }
    data = {k: v for k, v in data.items() if v is not None}

    result = await run_with_retry(
        client.table("programs").upsert(data, on_conflict="institution_id,name").execute()
    )
    return result.data[0] if result.data else None


async def upsert_admission_requirements(
    institution_id: str,
    program_id: str | None = None,
    olevel_subjects: list[str] | None = None,
    olevel_credits_min: int | None = None,
    utme_subjects: list[str] | None = None,
    minimum_jamb: int | None = None,
    minimum_credits: int | None = None,
    awaiting_result_accepted: bool | None = None,
    max_olevel_sittings: int | None = None,
    direct_entry_requirements: str | None = None,
    post_utme_required: bool | None = None,
    post_utme_format: str | None = None,
    post_utme_weight_pct: int | None = None,
    aggregate_formula: str | None = None,
) -> dict | None:
    """Upsert admission requirements."""
    client = await get_client()

    data = {
        "institution_id": institution_id,
        "program_id": program_id,
        "olevel_subjects": olevel_subjects,
        "olevel_credits_min": olevel_credits_min,
        "utme_subjects": utme_subjects,
        "minimum_jamb": minimum_jamb,
        "minimum_credits": minimum_credits,
        "awaiting_result_accepted": awaiting_result_accepted,
        "max_olevel_sittings": max_olevel_sittings,
        "direct_entry_requirements": direct_entry_requirements,
        "post_utme_required": post_utme_required,
        "post_utme_format": post_utme_format,
        "post_utme_weight_pct": post_utme_weight_pct,
        "aggregate_formula": aggregate_formula,
    }
    data = {k: v for k, v in data.items() if v is not None}

    conflict_key = "institution_id,program_id" if program_id else "institution_id"

    result = await run_with_retry(
        client.table("admission_requirements").upsert(data, on_conflict=conflict_key).execute()
    )
    return result.data[0] if result.data else None


async def upsert_olevel_rules(
    institution_id: str,
    program_id: str | None,
    subject: str,
    is_required: bool = True,
    min_grade: str = "C6",
    notes: str | None = None,
) -> dict | None:
    """Upsert O-Level subject rule."""
    client = await get_client()
    data = {
        "institution_id": institution_id,
        "program_id": program_id,
        "subject": subject,
        "is_required": is_required,
        "min_grade": min_grade,
        "notes": notes,
    }
    data = {k: v for k, v in data.items() if v is not None}

    result = await run_with_retry(
        client.table("olevel_rules").upsert(
            data, on_conflict="institution_id,program_id,subject"
        ).execute()
    )
    return result.data[0] if result.data else None


async def upsert_utme_rules(
    institution_id: str,
    program_id: str | None,
    subject: str,
    is_required: bool = True,
    notes: str | None = None,
) -> dict | None:
    """Upsert UTME subject rule."""
    client = await get_client()
    data = {
        "institution_id": institution_id,
        "program_id": program_id,
        "subject": subject,
        "is_required": is_required,
        "notes": notes,
    }
    data = {k: v for k, v in data.items() if v is not None}

    result = await run_with_retry(
        client.table("utme_rules").upsert(
            data, on_conflict="institution_id,program_id,subject"
        ).execute()
    )
    return result.data[0] if result.data else None


async def upsert_postutme_rules(
    institution_id: str,
    program_id: str | None,
    required: bool = True,
    format: str | None = None,
    weight_pct: int | None = None,
    min_score: int | None = None,
    details: str | None = None,
) -> dict | None:
    """Upsert Post-UTME rule."""
    client = await get_client()
    data = {
        "institution_id": institution_id,
        "program_id": program_id,
        "required": required,
        "format": format,
        "weight_pct": weight_pct,
        "min_score": min_score,
        "details": details,
    }
    data = {k: v for k, v in data.items() if v is not None}

    result = await run_with_retry(
        client.table("postutme_rules").upsert(
            data, on_conflict="institution_id,program_id"
        ).execute()
    )
    return result.data[0] if result.data else None


async def upsert_departmental_cutoff(
    institution_id: str,
    program_id: str | None,
    academic_session: str,
    merit_cutoff: int | None = None,
    catchment_cutoff: int | None = None,
    elds_cutoff: int | None = None,
    aggregate_formula: str | None = None,
    source_url: str | None = None,
    notes: str | None = None,
) -> dict | None:
    """Upsert departmental cutoff mark."""
    client = await get_client()
    data = {
        "institution_id": institution_id,
        "program_id": program_id,
        "academic_session": academic_session,
        "merit_cutoff": merit_cutoff,
        "catchment_cutoff": catchment_cutoff,
        "elds_cutoff": elds_cutoff,
        "aggregate_formula": aggregate_formula,
        "source_url": source_url,
        "notes": notes,
    }
    data = {k: v for k, v in data.items() if v is not None}

    result = await run_with_retry(
        client.table("departmental_cutoffs").upsert(
            data, on_conflict="institution_id,program_id,academic_session"
        ).execute()
    )
    return result.data[0] if result.data else None


async def upsert_catchment(
    institution_id: str,
    name: str,
    eligible_states: list[str] | None = None,
    policy: str = "geographical",
    details: str | None = None,
) -> dict | None:
    """Upsert catchment area."""
    client = await get_client()
    data = {
        "institution_id": institution_id,
        "name": name,
        "eligible_states": eligible_states,
        "policy": policy,
        "details": details,
    }
    data = {k: v for k, v in data.items() if v is not None}

    result = await run_with_retry(
        client.table("catchment").upsert(
            data, on_conflict="institution_id,name,policy"
        ).execute()
    )
    return result.data[0] if result.data else None


async def upsert_source_document(
    institution_id: str,
    url: str,
    document_type: str = "webpage",
    title: str | None = None,
    content_hash: str | None = None,
    date_published: str | None = None,
    confidence: str = "low",
    academic_session: str | None = None,
    raw_content: str | None = None,
) -> dict | None:
    """Upsert source document for provenance."""
    client = await get_client()
    data = {
        "institution_id": institution_id,
        "url": url,
        "document_type": document_type,
        "title": title,
        "content_hash": content_hash,
        "date_published": date_published,
        "confidence": confidence,
        "academic_session": academic_session,
        "raw_content": raw_content,
        "crawled_at": datetime.utcnow().isoformat(),
    }
    data = {k: v for k, v in data.items() if v is not None}

    result = await run_with_retry(
        client.table("source_documents").upsert(
            data, on_conflict="institution_id,url,crawled_at"
        ).execute()
    )
    return result.data[0] if result.data else None


async def log_crawl(
    institution_id: str | None,
    institution_name: str | None,
    url: str,
    status: str,
    confidence: str = "low",
    source_type: str = "webpage",
    academic_session: str | None = None,
    error_message: str | None = None,
    pages_crawled: int = 1,
    metadata: dict | None = None,
) -> dict | None:
    """Log crawl attempt for audit trail."""
    client = await get_client()

    data = {
        "institution_id": institution_id,
        "institution_name": institution_name,
        "url": url,
        "status": status,
        "confidence": confidence,
        "source_type": source_type,
        "academic_session": academic_session,
        "error_message": error_message,
        "pages_crawled": pages_crawled,
        "metadata": metadata,
        "crawled_at": datetime.utcnow().isoformat(),
    }
    data = {k: v for k, v in data.items() if v is not None}

    result = await run_with_retry(client.table("crawl_logs").insert(data).execute())
    return result.data[0] if result.data else None


async def store_raw_crawl(
    institution_name: str,
    url: str,
    raw_content: str,
    extracted_data: dict,
    academic_session: str | None = None,
) -> dict | None:
    """Store raw crawl data in staging table."""
    client = await get_client()
    content_hash = _generate_content_hash(extracted_data)

    data = {
        "institution_name": institution_name,
        "url": url,
        "raw_content": raw_content,
        "extracted_data": extracted_data,
        "content_hash": content_hash,
        "academic_session": academic_session,
        "status": "pending_review",
    }

    result = await run_with_retry(client.table("raw_crawl_data").insert(data).execute())
    return result.data[0] if result.data else None


async def promote_to_validated(
    raw_crawl_id: str,
    reviewer: str = "auto",
    notes: str | None = None,
) -> dict | None:
    """Move raw crawl data to validated_data after review."""
    client = await get_client()

    raw_result = await run_with_retry(
        client.table("raw_crawl_data").select("*").eq("id", raw_crawl_id).limit(1).execute()
    )
    if not raw_result.data:
        return None

    raw = raw_result.data[0]

    validated_data = {
        "raw_crawl_id": raw_crawl_id,
        "institution_name": raw["institution_name"],
        "url": raw["url"],
        "extracted_data": raw["extracted_data"],
        "content_hash": raw["content_hash"],
        "academic_session": raw["academic_session"],
        "reviewed_by": reviewer,
        "review_notes": notes,
        "status": "approved",
    }

    result = await run_with_retry(client.table("validated_data").insert(validated_data).execute())

    await run_with_retry(
        client.table("raw_crawl_data").update({
            "status": "validated",
            "reviewed_by": reviewer,
            "review_notes": notes,
            "reviewed_at": datetime.utcnow().isoformat(),
        }).eq("id", raw_crawl_id).execute()
    )

    return result.data[0] if result.data else None


async def reject_raw_crawl(
    raw_crawl_id: str,
    reviewer: str = "auto",
    notes: str | None = None,
) -> bool:
    """Mark raw crawl as rejected."""
    client = await get_client()
    result = await run_with_retry(
        client.table("raw_crawl_data").update({
            "status": "rejected",
            "reviewed_by": reviewer,
            "review_notes": notes,
            "reviewed_at": datetime.utcnow().isoformat(),
        }).eq("id", raw_crawl_id).execute()
    )
    return bool(result.data)


async def get_pending_validations(limit: int = 50) -> list[dict]:
    """Get raw crawl data pending review."""
    client = await get_client()
    result = await run_with_retry(
        client.table("raw_crawl_data")
        .select("*")
        .eq("status", "pending_review")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data or []


async def crawl_and_upsert_institution(
    institution: dict,
    programs: list[dict] | None = None,
    faculties: list[str] | None = None,
    admission_reqs: dict | None = None,
    cutoff_data: list[dict] | None = None,
    catchment_data: list[dict] | None = None,
    fee_tiers: list[dict] | None = None,
    sources: list[dict] | None = None,
    academic_session: str = "2025/2026",
) -> dict:
    """Atomically upsert a complete institution with all related data."""
    results: dict = {}

    inst = await upsert_institution(
        name=institution["name"],
        short_name=institution.get("short_name"),
        institution_type=institution.get("institution_type", "university"),
        ownership_type=institution.get("type", "federal"),
        state=institution.get("state"),
        city=institution.get("city"),
        website=institution.get("website"),
        admission_portal=institution.get("admission_portal") or (institution.get("application_process") or {}).get("portal_url"),
        year_established=institution.get("year_established"),
    )
    if not inst:
        raise RuntimeError(f"Failed to upsert institution: {institution['name']}")
    results["institution_id"] = inst["id"]
    inst_id = inst["id"]

    faculty_ids: dict = {}
    if faculties:
        for fac_name in faculties:
            fac = await upsert_faculty(inst_id, fac_name)
            if fac:
                faculty_ids[fac_name] = fac["id"]
    results["faculty_ids"] = faculty_ids

    program_ids: dict = {}
    if programs:
        for prog in programs:
            fac_id = faculty_ids.get(prog.get("faculty"))
            prog_record = await upsert_program(
                institution_id=inst_id,
                name=prog["name"],
                faculty_id=fac_id,
                degree=prog.get("degree"),
                level=prog.get("level"),
                duration_years=prog.get("duration_years"),
                affiliated_university=prog.get("affiliated_university"),
            )
            if prog_record:
                program_ids[prog["name"]] = prog_record["id"]
    results["program_ids"] = program_ids

    if admission_reqs:
        req = await upsert_admission_requirements(
            institution_id=inst_id,
            program_id=None,
            **admission_reqs,
        )
        if req:
            results["admission_requirements_id"] = req["id"]

    if programs and admission_reqs:
        for prog in programs:
            prog_reqs = prog.get("admission_requirements")
            if prog_reqs and prog.get("name") in program_ids:
                await upsert_admission_requirements(
                    institution_id=inst_id,
                    program_id=program_ids[prog["name"]],
                    **prog_reqs,
                )

    if cutoff_data:
        cutoff_ids: list = []
        for c in cutoff_data:
            prog_id = program_ids.get(c.get("program_name"))
            cutoff = await upsert_departmental_cutoff(
                institution_id=inst_id,
                program_id=prog_id,
                academic_session=academic_session,
                merit_cutoff=c.get("merit_cutoff"),
                catchment_cutoff=c.get("catchment_cutoff"),
                elds_cutoff=c.get("elds_cutoff"),
                aggregate_formula=c.get("aggregate_formula"),
                source_url=c.get("source_url"),
            )
            if cutoff:
                cutoff_ids.append(cutoff["id"])
        results["cutoff_ids"] = cutoff_ids

    if catchment_data:
        catchment_ids: list = []
        for c in catchment_data:
            catch = await upsert_catchment(
                institution_id=inst_id,
                name=c["name"],
                eligible_states=c.get("eligible_states"),
                policy=c.get("policy", "geographical"),
                details=c.get("details"),
            )
            if catch:
                catchment_ids.append(catch["id"])
        results["catchment_ids"] = catchment_ids

    if sources:
        source_ids: list = []
        for s in sources:
            src = await upsert_source_document(
                institution_id=inst_id,
                url=s["url"],
                document_type=s.get("document_type", "webpage"),
                title=s.get("title"),
                content_hash=s.get("content_hash"),
                confidence=s.get("confidence", "low"),
                academic_session=academic_session,
            )
            if src:
                source_ids.append(src["id"])
        results["source_ids"] = source_ids

    await log_crawl(
        institution_id=inst_id,
        institution_name=institution["name"],
        url=sources[0]["url"] if sources else institution.get("website", ""),
        status="success",
        confidence=institution.get("confidence", {}).get("overall", "low"),
        academic_session=academic_session,
        pages_crawled=len(sources) if sources else 1,
        metadata={"upsert_results": results},
    )

    return results


async def get_institution_by_name(name: str) -> dict | None:
    """Get institution by exact name match."""
    client = await get_client()
    result = await run_with_retry(
        client.table("institutions").select("*").eq("name", name).limit(1).execute()
    )
    return result.data[0] if result.data else None


async def get_programs_for_institution(institution_id: str) -> list[dict]:
    """Get all programs for an institution."""
    client = await get_client()
    result = await run_with_retry(
        client.table("programs").select("*").eq("institution_id", institution_id).execute()
    )
    return result.data or []


async def get_latest_cutoffs(institution_id: str, academic_session: str) -> list[dict]:
    """Get latest cutoffs for an institution."""
    client = await get_client()
    result = await run_with_retry(
        client.table("departmental_cutoffs")
        .select("*")
        .eq("institution_id", institution_id)
        .eq("academic_session", academic_session)
        .execute()
    )
    return result.data or []


async def get_crawl_logs(
    institution_name: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """Get crawl logs with optional filters."""
    client = await get_client()
    query = client.table("crawl_logs").select("*").order("crawled_at", desc=True).limit(limit)

    if institution_name:
        query = query.eq("institution_name", institution_name)
    if status:
        query = query.eq("status", status)

    result = await run_with_retry(query.execute())
    return result.data or []


async def upsert_crawl_run(
    gh_run_id: int,
    gh_run_url: str,
    status: str,
    inputs_json: dict | None = None,
    triggered_by: str | None = None,
    admin_email: str | None = None,
    metrics_json: dict | None = None,
    error_message: str | None = None,
) -> dict | None:
    """Upsert a crawl_run record keyed by gh_run_id (GitHub Actions run id)."""
    client = await get_client()

    data = {
        "gh_run_id": gh_run_id,
        "gh_run_url": gh_run_url,
        "status": status,
        "inputs_json": inputs_json,
        "triggered_by": triggered_by,
        "admin_email": admin_email,
        "metrics_json": metrics_json,
        "error_message": error_message,
    }
    if status == "in_progress" and inputs_json is not None:
        data["started_at"] = datetime.utcnow().isoformat()
    if status in ("success", "failure", "cancelled"):
        data["ended_at"] = datetime.utcnow().isoformat()
    data = {k: v for k, v in data.items() if v is not None}

    result = await run_with_retry(
        client.table("crawl_runs").upsert(data, on_conflict="gh_run_id").execute()
    )
    return result.data[0] if result.data else None
