"""Supabase Operations for Campus Compass Knowledge Acquisition Platform (CKAP).

Unified module replacing supabase_client.py + supabase_writer.py.
Provides async upserts for all 22 production tables + staging layer + knowledge versioning.
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

# ============================================================================
# CONFIGURATION
# ============================================================================

class SupabaseConfig:
    def __init__(self) -> None:
        self.url = os.getenv("SUPABASE_URL")
        self.anon_key = os.getenv("SUPABASE_ANON_KEY")
        self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.storage_bucket = os.getenv("SUPABASE_STORAGE_BUCKET", "crawl-assets")
    
    def validate(self) -> bool:
        return all([self.url, self.anon_key, self.service_role_key])


_client: AsyncClient | None = None
_service_client: AsyncClient | None = None


def _get_config() -> SupabaseConfig:
    return SupabaseConfig()


async def get_client(use_service_role: bool = False) -> AsyncClient:
    """Get or create async Supabase client."""
    global _client, _service_client
    
    if use_service_role:
        if _service_client is None:
            cfg = _get_config()
            if not cfg.validate():
                raise RuntimeError(
                    "Supabase not configured. Check SUPABASE_URL, SUPABASE_ANON_KEY, "
                    "SUPABASE_SERVICE_ROLE_KEY in .env"
                )
            _service_client = await create_client(cfg.url, cfg.service_role_key)
        return _service_client
    else:
        if _client is None:
            cfg = _get_config()
            if not cfg.validate():
                raise RuntimeError("Supabase not configured")
            _client = await create_client(cfg.url, cfg.anon_key)
        return _client


async def close_clients() -> None:
    """Close client connections - no-op as AsyncClient manages its own connections."""
    pass


# ============================================================================
# UTILITIES
# ============================================================================

async def run_with_retry(coro_factory, max_retries: int = 3, base_delay: float = 1.0) -> Any:
    """Run async operation with exponential backoff retry.
    
    Args:
        coro_factory: A callable that returns a new coroutine each time (e.g., lambda: client.table(...).execute())
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
    """
    last_exc = None
    for attempt in range(max_retries):
        try:
            return await coro_factory()
        except (TimeoutError, APIError) as e:
            last_exc = e
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
            continue
    raise last_exc


def _generate_content_hash(data: dict) -> str:
    """Generate SHA256 hash of normalized content for change detection."""
    normalized = {k: v for k, v in data.items() 
                  if k not in ("crawled_at", "last_updated", "id", "created_at", "updated_at", "version_number")}
    serialized = json.dumps(normalized, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()[:32]


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


# ============================================================================
# PRODUCTION TABLE UPSERTS (all 22 tables)
# ============================================================================

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
    jamb_code: str | None = None,
    contact_email: str | None = None,
    phone: str | None = None,
    address: str | None = None,
    accreditation_body: str | None = None,
) -> dict | None:
    client = await get_client(use_service_role=True)
    data = {
        "name": name, "short_name": short_name, "institution_type": institution_type,
        "ownership_type": ownership_type, "state": state, "city": city, "website": website,
        "admission_portal": admission_portal, "year_established": year_established,
        "jamb_code": jamb_code, "contact_email": contact_email, "phone": phone,
        "address": address, "accreditation_body": accreditation_body,
        "last_updated": _now_iso(),
    }
    data = {k: v for k, v in data.items() if v is not None}
    
    result = await run_with_retry(
        lambda: client.table("institutions").upsert(data, on_conflict="name").execute()
    )
    return result.data[0] if result.data else None


async def upsert_faculty(
    institution_id: str,
    name: str,
    short_name: str | None = None,
) -> dict | None:
    client = await get_client(use_service_role=True)
    data = {"institution_id": institution_id, "name": name, "short_name": short_name}
    data = {k: v for k, v in data.items() if v is not None}
    result = await run_with_retry(
        lambda: client.table("faculties").upsert(data, on_conflict="institution_id,name").execute()
    )
    return result.data[0] if result.data else None


async def upsert_department(
    faculty_id: str,
    institution_id: str,
    name: str,
    short_name: str | None = None,
    code: str | None = None,
) -> dict | None:
    client = await get_client(use_service_role=True)
    data = {"faculty_id": faculty_id, "institution_id": institution_id, "name": name, "short_name": short_name, "code": code}
    data = {k: v for k, v in data.items() if v is not None}
    result = await run_with_retry(
        lambda: client.table("departments").upsert(data, on_conflict="faculty_id,name").execute()
    )
    return result.data[0] if result.data else None


async def upsert_course(
    institution_id: str,
    name: str,
    department_id: str | None = None,
    faculty_id: str | None = None,
    degree: str | None = None,
    level: str | None = None,
    duration_years: int | None = None,
    affiliated_university: str | None = None,
    jamb_subject_combination: list[str] | None = None,
) -> dict | None:
    client = await get_client(use_service_role=True)
    data = {
        "institution_id": institution_id, "department_id": department_id, "faculty_id": faculty_id,
        "name": name, "degree": degree, "level": level, "duration_years": duration_years,
        "affiliated_university": affiliated_university, "jamb_subject_combination": jamb_subject_combination,
    }
    data = {k: v for k, v in data.items() if v is not None}
    result = await run_with_retry(
        lambda: client.table("courses").upsert(data, on_conflict="institution_id,name").execute()
    )
    return result.data[0] if result.data else None


async def upsert_course_alias(
    canonical_course_id: str,
    alias: str,
    alias_type: str = "abbreviation",
) -> dict | None:
    client = await get_client(use_service_role=True)
    data = {"canonical_course_id": canonical_course_id, "alias": alias, "alias_type": alias_type}
    result = await run_with_retry(
        lambda: client.table("course_aliases").upsert(data, on_conflict="canonical_course_id,alias").execute()
    )
    return result.data[0] if result.data else None


async def upsert_subject(
    name: str,
    code: str | None = None,
    subject_category: str | None = None,
) -> dict | None:
    client = await get_client(use_service_role=True)
    data = {"name": name, "code": code, "subject_category": subject_category}
    data = {k: v for k, v in data.items() if v is not None}
    result = await run_with_retry(
        lambda: client.table("subjects").upsert(data, on_conflict="name").execute()
    )
    return result.data[0] if result.data else None


async def upsert_subject_alias(
    canonical_subject_id: str,
    alias: str,
) -> dict | None:
    client = await get_client(use_service_role=True)
    data = {"canonical_subject_id": canonical_subject_id, "alias": alias}
    result = await run_with_retry(
        lambda: client.table("subject_aliases").upsert(data, on_conflict="canonical_subject_id,alias").execute()
    )
    return result.data[0] if result.data else None


async def upsert_admission_requirements(
    institution_id: str,
    course_id: str | None = None,
    olevel_credits_min: int | None = None,
    olevel_sittings_max: int = 2,
    awaiting_result_accepted: bool = True,
    direct_entry_requirements: str | None = None,
    minimum_jamb: int | None = None,
    post_utme_required: bool | None = None,
    post_utme_format: str | None = None,
    post_utme_weight_pct: int | None = None,
    aggregate_formula: str | None = None,
) -> dict | None:
    client = await get_client(use_service_role=True)
    data = {
        "institution_id": institution_id, "course_id": course_id,
        "olevel_credits_min": olevel_credits_min, "olevel_sittings_max": olevel_sittings_max,
        "awaiting_result_accepted": awaiting_result_accepted,
        "direct_entry_requirements": direct_entry_requirements, "minimum_jamb": minimum_jamb,
        "post_utme_required": post_utme_required, "post_utme_format": post_utme_format,
        "post_utme_weight_pct": post_utme_weight_pct, "aggregate_formula": aggregate_formula,
    }
    data = {k: v for k, v in data.items() if v is not None}
    
    conflict_key = "institution_id,course_id" if course_id else "institution_id"
    result = await run_with_retry(
        lambda: client.table("admission_requirements").upsert(data, on_conflict=conflict_key).execute()
    )
    return result.data[0] if result.data else None


async def upsert_olevel_requirements(
    admission_requirement_id: str,
    subject_id: str,
    is_required: bool = True,
    min_grade: str = "C6",
    notes: str | None = None,
) -> dict | None:
    client = await get_client(use_service_role=True)
    data = {"admission_requirement_id": admission_requirement_id, "subject_id": subject_id,
            "is_required": is_required, "min_grade": min_grade, "notes": notes}
    data = {k: v for k, v in data.items() if v is not None}
    result = await run_with_retry(
        lambda: client.table("olevel_requirements").upsert(data, on_conflict="admission_requirement_id,subject_id").execute()
    )
    return result.data[0] if result.data else None


async def upsert_utme_requirements(
    admission_requirement_id: str,
    subject_id: str,
    is_required: bool = True,
    is_compulsory: bool = False,
    notes: str | None = None,
) -> dict | None:
    client = await get_client(use_service_role=True)
    data = {"admission_requirement_id": admission_requirement_id, "subject_id": subject_id,
            "is_required": is_required, "is_compulsory": is_compulsory, "notes": notes}
    data = {k: v for k, v in data.items() if v is not None}
    result = await run_with_retry(
        lambda: client.table("utme_requirements").upsert(data, on_conflict="admission_requirement_id,subject_id").execute()
    )
    return result.data[0] if result.data else None


async def upsert_direct_entry(
    admission_requirement_id: str,
    qualification_type: str,
    qualification_subject: str | None = None,
    min_grade: str | None = None,
    min_cgpa: float | None = None,
    accepts_ijmb: bool = False,
    accepts_jupeb: bool = False,
    notes: str | None = None,
) -> dict | None:
    client = await get_client(use_service_role=True)
    data = {
        "admission_requirement_id": admission_requirement_id, "qualification_type": qualification_type,
        "qualification_subject": qualification_subject, "min_grade": min_grade,
        "min_cgpa": min_cgpa, "accepts_ijmb": accepts_ijmb, "accepts_jupeb": accepts_jupeb, "notes": notes,
    }
    data = {k: v for k, v in data.items() if v is not None}
    result = await run_with_retry(lambda: client.table("direct_entry").insert(data).execute())
    return result.data[0] if result.data else None


async def upsert_post_utme(
    admission_requirement_id: str,
    required: bool = True,
    format: str | None = None,
    weight_pct: int | None = None,
    min_score: int | None = None,
    duration_minutes: int | None = None,
    subjects: list[str] | None = None,
    past_questions_url: str | None = None,
    notes: str | None = None,
) -> dict | None:
    client = await get_client(use_service_role=True)
    data = {
        "admission_requirement_id": admission_requirement_id, "required": required, "format": format,
        "weight_pct": weight_pct, "min_score": min_score, "duration_minutes": duration_minutes,
        "subjects": subjects, "past_questions_url": past_questions_url, "notes": notes,
    }
    data = {k: v for k, v in data.items() if v is not None}
    result = await run_with_retry(
        lambda: client.table("post_utme").upsert(data, on_conflict="admission_requirement_id").execute()
    )
    return result.data[0] if result.data else None


async def upsert_aggregate_formula(
    institution_id: str,
    formula_text: str,
    formula_json: dict | None = None,
    course_id: str | None = None,
    effective_from: str = "2025/2026",
    effective_to: str | None = None,
    is_default: bool = False,
) -> dict | None:
    client = await get_client(use_service_role=True)
    data = {
        "institution_id": institution_id, "course_id": course_id, "formula_text": formula_text,
        "formula_json": formula_json, "effective_from": effective_from, "effective_to": effective_to,
        "is_default": is_default,
    }
    data = {k: v for k, v in data.items() if v is not None}
    result = await run_with_retry(
        lambda: client.table("aggregate_formulas").upsert(data, on_conflict="institution_id,course_id,effective_from").execute()
    )
    return result.data[0] if result.data else None


async def upsert_departmental_cutoff(
    institution_id: str,
    academic_session: str,
    course_id: str | None = None,
    merit_cutoff: float | None = None,
    catchment_cutoff: float | None = None,
    elds_cutoff: float | None = None,
    aggregate_formula_id: str | None = None,
    source_url: str | None = None,
    notes: str | None = None,
    confidence: str = "low",
) -> dict | None:
    client = await get_client(use_service_role=True)
    data = {
        "institution_id": institution_id, "course_id": course_id, "academic_session": academic_session,
        "merit_cutoff": merit_cutoff, "catchment_cutoff": catchment_cutoff, "elds_cutoff": elds_cutoff,
        "aggregate_formula_id": aggregate_formula_id, "source_url": source_url, "notes": notes,
        "confidence": confidence,
    }
    data = {k: v for k, v in data.items() if v is not None}
    result = await run_with_retry(
        lambda: client.table("departmental_cutoffs").upsert(data, on_conflict="institution_id,course_id,academic_session").execute()
    )
    return result.data[0] if result.data else None


async def upsert_catchment(
    institution_id: str,
    name: str,
    eligible_states: list[str] | None = None,
    policy: str = "geographical",
    details: str | None = None,
) -> dict | None:
    client = await get_client(use_service_role=True)
    data = {"institution_id": institution_id, "name": name, "eligible_states": eligible_states,
            "policy": policy, "details": details}
    data = {k: v for k, v in data.items() if v is not None}
    result = await run_with_retry(
        lambda: client.table("catchment").upsert(data, on_conflict="institution_id,name,policy").execute()
    )
    return result.data[0] if result.data else None


async def upsert_fees(
    institution_id: str,
    academic_session: str,
    fee_category: str,
    amount_ngn: int,
    course_id: str | None = None,
    faculty_id: str | None = None,
    amount_usd: int | None = None,
    currency: str = "NGN",
    indigene_amount_ngn: int | None = None,
    non_indigene_amount_ngn: int | None = None,
    is_per_session: bool = True,
    payment_schedule: str | None = None,
    source_url: str | None = None,
    notes: str | None = None,
) -> dict | None:
    client = await get_client(use_service_role=True)
    data = {
        "institution_id": institution_id, "course_id": course_id, "faculty_id": faculty_id,
        "fee_category": fee_category, "amount_ngn": amount_ngn, "amount_usd": amount_usd,
        "currency": currency, "indigene_amount_ngn": indigene_amount_ngn,
        "non_indigene_amount_ngn": non_indigene_amount_ngn, "academic_session": academic_session,
        "is_per_session": is_per_session, "payment_schedule": payment_schedule,
        "source_url": source_url, "notes": notes,
    }
    data = {k: v for k, v in data.items() if v is not None}
    result = await run_with_retry(
        lambda: client.table("fees").upsert(
            data, on_conflict="institution_id,course_id,faculty_id,fee_category,academic_session"
        ).execute()
    )
    return result.data[0] if result.data else None


async def upsert_deadline(
    institution_id: str,
    deadline_type: str,
    deadline_date: str,
    academic_session: str,
    course_id: str | None = None,
    is_extended: bool = False,
    extension_date: str | None = None,
    source_url: str | None = None,
    notes: str | None = None,
) -> dict | None:
    client = await get_client(use_service_role=True)
    data = {
        "institution_id": institution_id, "course_id": course_id, "deadline_type": deadline_type,
        "deadline_date": deadline_date, "academic_session": academic_session, "is_extended": is_extended,
        "extension_date": extension_date, "source_url": source_url, "notes": notes,
    }
    data = {k: v for k, v in data.items() if v is not None}
    result = await run_with_retry(
        lambda: client.table("deadlines").upsert(
            data, on_conflict="institution_id,course_id,deadline_type,academic_session"
        ).execute()
    )
    return result.data[0] if result.data else None


async def upsert_admission_news(
    title: str,
    source_url: str,
    institution_id: str | None = None,
    content: str | None = None,
    summary: str | None = None,
    published_date: str | None = None,
    news_category: str | None = None,
    is_critical: bool = False,
    content_hash: str | None = None,
) -> dict | None:
    client = await get_client(use_service_role=True)
    data = {
        "institution_id": institution_id, "title": title, "source_url": source_url, "content": content,
        "summary": summary, "published_date": published_date, "news_category": news_category,
        "is_critical": is_critical, "content_hash": content_hash,
    }
    data = {k: v for k, v in data.items() if v is not None}
    result = await run_with_retry(
        lambda: client.table("admission_news").upsert(data, on_conflict="source_url,content_hash").execute()
    )
    return result.data[0] if result.data else None


async def upsert_source_document(
    institution_id: str,
    url: str,
    document_type: str = "webpage",
    course_id: str | None = None,
    title: str | None = None,
    storage_path: str | None = None,
    storage_bucket: str = "crawl-assets",
    content_hash: str | None = None,
    date_published: str | None = None,
    confidence: str = "low",
    academic_session: str | None = None,
    raw_content: str | None = None,
    extracted_data: dict | None = None,
    file_size_bytes: int | None = None,
    mime_type: str | None = None,
) -> dict | None:
    client = await get_client(use_service_role=True)
    data = {
        "institution_id": institution_id, "course_id": course_id, "url": url,
        "document_type": document_type, "title": title, "storage_path": storage_path,
        "storage_bucket": storage_bucket, "content_hash": content_hash,
        "date_published": date_published, "confidence": confidence, "academic_session": academic_session,
        "raw_content": raw_content[:50000] if raw_content else None,
        "extracted_data": extracted_data, "file_size_bytes": file_size_bytes, "mime_type": mime_type,
    }
    data = {k: v for k, v in data.items() if v is not None}
    result = await run_with_retry(
        lambda: client.table("source_documents").upsert(data, on_conflict="institution_id,url,crawled_at").execute()
    )
    return result.data[0] if result.data else None


async def log_crawl(
    institution_id: str | None = None,
    institution_name: str | None = None,
    course_id: str | None = None,
    url: str = "",
    status: str = "success",
    confidence: str = "low",
    source_type: str = "webpage",
    academic_session: str | None = None,
    error_message: str | None = None,
    pages_crawled: int = 1,
    metadata: dict | None = None,
    storage_paths: list[str] | None = None,
) -> dict | None:
    client = await get_client(use_service_role=True)
    data = {
        "institution_id": institution_id, "institution_name": institution_name, "course_id": course_id,
        "url": url, "status": status, "confidence": confidence, "source_type": source_type,
        "academic_session": academic_session, "error_message": error_message, "pages_crawled": pages_crawled,
        "metadata": metadata or {}, "storage_paths": storage_paths or [],
    }
    data = {k: v for k, v in data.items() if v is not None}
    result = await run_with_retry(lambda: client.table("crawl_logs").insert(data).execute())
    return result.data[0] if result.data else None


async def record_knowledge_version(
    table_name: str,
    record_id: str,
    institution_id: str | None,
    version_number: int,
    effective_date: str,
    new_value: dict,
    previous_value: dict | None = None,
    changed_fields: list[str] | None = None,
    source_document_id: str | None = None,
    crawl_log_id: str | None = None,
    change_reason: str = "crawl",
    created_by: str = "crawler",
) -> dict | None:
    client = await get_client(use_service_role=True)
    data = {
        "table_name": table_name, "record_id": record_id, "institution_id": institution_id,
        "version_number": version_number, "effective_date": effective_date,
        "previous_value": previous_value, "new_value": new_value, "changed_fields": changed_fields or [],
        "source_document_id": source_document_id, "crawl_log_id": crawl_log_id,
        "change_reason": change_reason, "created_by": created_by,
    }
    data = {k: v for k, v in data.items() if v is not None}
    result = await run_with_retry(lambda: client.table("knowledge_versions").insert(data).execute())
    return result.data[0] if result.data else None


# ============================================================================
# STAGING LAYER
# ============================================================================

async def stage_raw_crawl(
    institution_name: str,
    url: str,
    raw_content: str,
    extracted_data: dict,
    institution_id: str | None = None,
    course_name: str | None = None,
    course_id: str | None = None,
    academic_session: str | None = None,
) -> dict | None:
    client = await get_client(use_service_role=True)
    content_hash = _generate_content_hash(extracted_data)
    data = {
        "institution_name": institution_name, "institution_id": institution_id,
        "course_name": course_name, "course_id": course_id, "url": url,
        "raw_content": raw_content[:50000], "extracted_data": extracted_data,
        "content_hash": content_hash, "academic_session": academic_session, "status": "pending_review",
    }
    data = {k: v for k, v in data.items() if v is not None}
    result = await run_with_retry(lambda: client.table("raw_crawl_data").insert(data).execute())
    return result.data[0] if result.data else None


async def promote_to_validated(
    raw_crawl_id: str,
    reviewed_by: str = "auto",
    review_notes: str | None = None,
) -> dict | None:
    client = await get_client(use_service_role=True)
    raw_result = await run_with_retry(
        lambda: client.table("raw_crawl_data").select("*").eq("id", raw_crawl_id).limit(1).execute()
    )
    if not raw_result.data:
        return None
    
    raw = raw_result.data[0]
    validated_data = {
        "raw_crawl_id": raw_crawl_id, "institution_name": raw["institution_name"],
        "institution_id": raw.get("institution_id"), "course_name": raw.get("course_name"),
        "course_id": raw.get("course_id"), "url": raw["url"], "extracted_data": raw["extracted_data"],
        "content_hash": raw["content_hash"], "academic_session": raw.get("academic_session"),
        "reviewed_by": reviewed_by, "review_notes": review_notes, "status": "approved",
    }
    result = await run_with_retry(lambda: client.table("validated_data").insert(validated_data).execute())
    
    await run_with_retry(
        lambda: client.table("raw_crawl_data").update({
            "status": "validated", "reviewed_by": reviewed_by,
            "review_notes": review_notes, "reviewed_at": _now_iso()
        }).eq("id", raw_crawl_id).execute()
    )
    return result.data[0] if result.data else None


async def reject_raw_crawl(
    raw_crawl_id: str,
    reviewed_by: str = "auto",
    review_notes: str | None = None,
) -> bool:
    client = await get_client(use_service_role=True)
    result = await run_with_retry(
        lambda: client.table("raw_crawl_data").update({
            "status": "rejected", "reviewed_by": reviewed_by,
            "review_notes": review_notes, "reviewed_at": _now_iso()
        }).eq("id", raw_crawl_id).execute()
    )
    return bool(result.data)


async def get_pending_validations(limit: int = 50) -> list[dict]:
    client = await get_client(use_service_role=True)
    result = await run_with_retry(
        lambda: client.table("raw_crawl_data")
        .select("*").eq("status", "pending_review").order("created_at", desc=True).limit(limit).execute()
    )
    return result.data or []


# ============================================================================
# HIGH-LEVEL: Full Institution Upsert
# ============================================================================

async def upsert_full_institution(
    institution: dict,
    programs: list[dict] | None = None,
    faculties: list[str] | None = None,
    admission_reqs: dict | None = None,
    cutoff_data: list[dict] | None = None,
    catchment_data: list[dict] | None = None,
    fee_tiers: list[dict] | None = None,
    deadlines_data: list[dict] | None = None,
    sources: list[dict] | None = None,
    academic_session: str = "2025/2026",
) -> dict:
    """Atomically upsert a complete institution with all related data."""
    results = {}
    
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
        jamb_code=institution.get("jamb_code"),
        contact_email=institution.get("contact_email"),
        phone=institution.get("phone"),
        address=institution.get("address"),
        accreditation_body=institution.get("accreditation_body"),
    )
    if not inst:
        raise RuntimeError(f"Failed to upsert institution: {institution['name']}")
    results["institution_id"] = inst["id"]
    inst_id = inst["id"]
    
    faculty_ids = {}
    if faculties:
        for fac_name in faculties:
            fac = await upsert_faculty(inst_id, fac_name)
            if fac:
                faculty_ids[fac_name] = fac["id"]
    results["faculty_ids"] = faculty_ids
    
    program_ids = {}
    if programs:
        for prog in programs:
            fac_id = faculty_ids.get(prog.get("faculty"))
            prog_rec = await upsert_course(
                institution_id=inst_id, name=prog["name"], faculty_id=fac_id,
                degree=prog.get("degree"), level=prog.get("level"),
                duration_years=prog.get("duration_years"),
                affiliated_university=prog.get("affiliated_university"),
                jamb_subject_combination=prog.get("jamb_subject_combination"),
            )
            if prog_rec:
                program_ids[prog["name"]] = prog_rec["id"]
    results["program_ids"] = program_ids
    
    if admission_reqs:
        req = await upsert_admission_requirements(institution_id=inst_id, course_id=None, **admission_reqs)
        if req:
            results["admission_requirements_id"] = req["id"]
    
    if programs and admission_reqs:
        for prog in programs:
            prog_reqs = prog.get("admission_requirements")
            if prog_reqs and prog.get("name") in program_ids:
                await upsert_admission_requirements(
                    institution_id=inst_id, course_id=program_ids[prog["name"]], **prog_reqs
                )
    
    if cutoff_data:
        cutoff_ids = []
        for c in cutoff_data:
            prog_id = program_ids.get(c.get("program_name"))
            cutoff = await upsert_departmental_cutoff(
                institution_id=inst_id, academic_session=academic_session, course_id=prog_id,
                merit_cutoff=c.get("merit_cutoff"), catchment_cutoff=c.get("catchment_cutoff"),
                elds_cutoff=c.get("elds_cutoff"), aggregate_formula=c.get("aggregate_formula"),
                source_url=c.get("source_url"),
            )
            if cutoff:
                cutoff_ids.append(cutoff["id"])
        results["cutoff_ids"] = cutoff_ids
    
    if catchment_data:
        catchment_ids = []
        for c in catchment_data:
            catch = await upsert_catchment(
                institution_id=inst_id, name=c["name"], eligible_states=c.get("eligible_states"),
                policy=c.get("policy", "geographical"), details=c.get("details"),
            )
            if catch:
                catchment_ids.append(catch["id"])
        results["catchment_ids"] = catchment_ids
    
    if fee_tiers:
        fee_ids = []
        for f in fee_tiers:
            prog_id = program_ids.get(f.get("program_or_faculty"))
            fac_id = faculty_ids.get(f.get("program_or_faculty"))
            fee = await upsert_fees(
                institution_id=inst_id, academic_session=academic_session,
                fee_category=f.get("fee_category", "tuition"), amount_ngn=f["tuition_per_session_ngn"],
                course_id=prog_id, faculty_id=fac_id, amount_usd=f.get("tuition_per_session_usd"),
                currency=f.get("currency", "NGN"),
                indigene_amount_ngn=f.get("indigene_vs_non_indigene", {}).get("indigene") if f.get("indigene_vs_non_indigene") else None,
                non_indigene_amount_ngn=f.get("indigene_vs_non_indigene", {}).get("non_indigene") if f.get("indigene_vs_non_indigene") else None,
                is_per_session=True, payment_schedule=f.get("payment_schedule"),
                source_url=f.get("source_url"),
            )
            if fee:
                fee_ids.append(fee["id"])
        results["fee_ids"] = fee_ids
    
    if deadlines_data:
        deadline_ids = []
        for d in deadlines_data:
            prog_id = program_ids.get(d.get("course_name"))
            dl = await upsert_deadline(
                institution_id=inst_id, deadline_type=d["deadline_type"],
                deadline_date=d["deadline_date"], academic_session=academic_session,
                course_id=prog_id, is_extended=d.get("is_extended", False),
                extension_date=d.get("extension_date"), source_url=d.get("source_url"),
                notes=d.get("notes"),
            )
            if dl:
                deadline_ids.append(dl["id"])
        results["deadline_ids"] = deadline_ids
    
    if sources:
        source_ids = []
        for s in sources:
            src = await upsert_source_document(
                institution_id=inst_id, url=s["url"], document_type=s.get("document_type", "webpage"),
                title=s.get("title"), storage_path=s.get("storage_path"),
                storage_bucket=s.get("storage_bucket", "crawl-assets"),
                content_hash=s.get("content_hash"), date_published=s.get("date_published"),
                confidence=s.get("confidence", "low"), academic_session=academic_session,
                raw_content=s.get("raw_content"), extracted_data=s.get("extracted_data"),
            )
            if src:
                source_ids.append(src["id"])
        results["source_ids"] = source_ids
    
    await log_crawl(
        institution_id=inst_id, institution_name=institution["name"],
        url=(sources or [{}])[0].get("url") if sources else institution.get("website", ""),
        status="success", confidence=institution.get("confidence", {}).get("overall", "low"),
        academic_session=academic_session, pages_crawled=len(sources) if sources else 1,
        metadata={"upsert_results": results},
        storage_paths=[s.get("storage_path") for s in (sources or []) if s.get("storage_path")],
    )
    
    return results


# ============================================================================
# QUERY HELPERS
# ============================================================================

async def get_institution_by_name(name: str) -> dict | None:
    client = await get_client(use_service_role=True)
    result = await run_with_retry(
        lambda: client.table("institutions").select("*").eq("name", name).limit(1).execute()
    )
    return result.data[0] if result.data else None


async def get_programs_for_institution(institution_id: str) -> list[dict]:
    client = await get_client(use_service_role=True)
    result = await run_with_retry(
        lambda: client.table("courses").select("*").eq("institution_id", institution_id).execute()
    )
    return result.data or []


async def get_latest_cutoffs(institution_id: str, academic_session: str) -> list[dict]:
    client = await get_client(use_service_role=True)
    result = await run_with_retry(
        lambda: client.table("departmental_cutoffs")
        .select("*, courses(name)")
        .eq("institution_id", institution_id).eq("academic_session", academic_session).execute()
    )
    return result.data or []


async def get_crawl_logs(
    institution_name: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict]:
    client = await get_client(use_service_role=True)
    query = client.table("crawl_logs").select("*").order("crawled_at", desc=True).limit(limit)
    if institution_name:
        query = query.eq("institution_name", institution_name)
    if status:
        query = query.eq("status", status)
    result = await run_with_retry(lambda: query.execute())
    return result.data or []


# ============================================================================
# MIGRATION HELPERS: KB schema -> Unified schema
# ============================================================================

async def migrate_kb_to_unified(kb_db_path: str) -> dict:
    """Migrate data from legacy KB SQLite (7 tables) to unified Supabase schema."""
    import sqlite3
    
    conn = sqlite3.connect(kb_db_path)
    conn.row_factory = sqlite3.Row
    stats = {}
    
    def row_to_dict(row: sqlite3.Row) -> dict:
        return {k: row[k] for k in row.keys()}
    
    # Build name -> UUID mapping for institutions after initial upsert
    inst_name_to_uuid = {}
    
    try:
        insts = conn.execute("SELECT * FROM kb_institutions").fetchall()
        for inst in insts:
            inst_d = row_to_dict(inst)
            result = await upsert_institution(
                name=inst_d["name"], short_name=inst_d.get("short_name"),
                institution_type=inst_d["institution_type"], ownership_type=inst_d["ownership_type"],
                state=inst_d.get("state"), city=inst_d.get("city"), website=inst_d.get("website"),
                admission_portal=inst_d.get("admission_portal"), year_established=inst_d.get("year_established"),
            )
            if result:
                inst_name_to_uuid[inst_d["name"]] = result["id"]
        stats["institutions"] = len(insts)
        
        facs = conn.execute("SELECT * FROM kb_faculties").fetchall()
        for fac in facs:
            fac_d = row_to_dict(fac)
            inst_row = conn.execute("SELECT name FROM kb_institutions WHERE id = ?", (fac_d["institution_id"],)).fetchone()
            if inst_row:
                inst_name = inst_row["name"]
                inst_uuid = inst_name_to_uuid.get(inst_name)
                if inst_uuid:
                    await upsert_faculty(inst_uuid, fac_d["name"])
        stats["faculties"] = len(facs)
        
        progs = conn.execute("SELECT * FROM kb_programs").fetchall()
        for prog in progs:
            prog_d = row_to_dict(prog)
            inst_row = conn.execute("SELECT name FROM kb_institutions WHERE id = ?", (prog_d["institution_id"],)).fetchone()
            fac_row = conn.execute("SELECT name FROM kb_faculties WHERE id = ?", (prog_d["faculty_id"],)).fetchone() if prog_d.get("faculty_id") else None
            
            inst_uuid = inst_name_to_uuid.get(inst_row["name"]) if inst_row else None
            fac_uuid = None
            if inst_uuid and fac_row:
                # Need to get faculty UUID from Supabase
                fac_result = await get_client(use_service_role=True)
                fac_query = fac_result.table("faculties").select("id").eq("institution_id", inst_uuid).eq("name", fac_row["name"]).execute()
                if fac_query.data:
                    fac_uuid = fac_query.data[0]["id"]
            
            if inst_uuid:
                await upsert_course(
                    institution_id=inst_uuid, name=prog_d["name"], faculty_id=fac_uuid,
                    degree=prog_d.get("degree"), level=prog_d.get("level"),
                    duration_years=prog_d.get("duration_years"),
                    affiliated_university=prog_d.get("affiliated_university"),
                )
        stats["programs"] = len(progs)
        
        reqs = conn.execute("SELECT * FROM kb_admission_requirements").fetchall()
        for req in reqs:
            req_d = row_to_dict(req)
            inst_row = conn.execute("SELECT name FROM kb_institutions WHERE id = ?", (req_d["institution_id"],)).fetchone()
            prog_row = conn.execute("SELECT name FROM kb_programs WHERE id = ?", (req_d["program_id"],)).fetchone() if req_d.get("program_id") else None
            
            inst_uuid = inst_name_to_uuid.get(inst_row["name"]) if inst_row else None
            prog_uuid = None
            if inst_uuid and prog_row:
                prog_result = await get_client(use_service_role=True)
                pq = prog_result.table("courses").select("id").eq("institution_id", inst_uuid).eq("name", prog_row["name"]).execute()
                if pq.data:
                    prog_uuid = pq.data[0]["id"]
            
            if inst_uuid:
                await upsert_admission_requirements(
                    institution_id=inst_uuid, course_id=prog_uuid,
                    olevel_credits_min=req_d.get("olevel_credits_min"), minimum_jamb=req_d.get("minimum_jamb"),
                    direct_entry_requirements=req_d.get("direct_entry_requirements"),
                    post_utme_required=req_d.get("post_utme_required"), post_utme_format=req_d.get("post_utme_format"),
                    post_utme_weight_pct=req_d.get("post_utme_weight_pct"), aggregate_formula=req_d.get("aggregate_formula"),
                )
        stats["admission_requirements"] = len(reqs)
        
        cutoffs = conn.execute("SELECT * FROM kb_cutoff_marks").fetchall()
        for c in cutoffs:
            c_d = row_to_dict(c)
            inst_row = conn.execute("SELECT name FROM kb_institutions WHERE id = ?", (c_d["institution_id"],)).fetchone()
            prog_row = conn.execute("SELECT name FROM kb_programs WHERE id = ?", (c_d["program_id"],)).fetchone() if c_d.get("program_id") else None
            
            inst_uuid = inst_name_to_uuid.get(inst_row["name"]) if inst_row else None
            prog_uuid = None
            if inst_uuid and prog_row:
                prog_result = await get_client(use_service_role=True)
                pq = prog_result.table("courses").select("id").eq("institution_id", inst_uuid).eq("name", prog_row["name"]).execute()
                if pq.data:
                    prog_uuid = pq.data[0]["id"]
            
            if inst_uuid:
                await upsert_departmental_cutoff(
                    institution_id=inst_uuid, academic_session=c_d["academic_year"], course_id=prog_uuid,
                    merit_cutoff=c_d.get("merit_cutoff"), catchment_cutoff=c_d.get("catchment_cutoff"),
                    elds_cutoff=c_d.get("elds_cutoff"), aggregate_formula=c_d.get("aggregate_formula"),
                    source_url=c_d.get("source_url"),
                )
        stats["cutoffs"] = len(cutoffs)
        
        catchments = conn.execute("SELECT * FROM kb_catchment_areas").fetchall()
        for c in catchments:
            c_d = row_to_dict(c)
            inst_row = conn.execute("SELECT name FROM kb_institutions WHERE id = ?", (c_d["institution_id"],)).fetchone()
            if inst_row:
                inst_uuid = inst_name_to_uuid.get(inst_row["name"])
                if inst_uuid:
                    eligible_states = json.loads(c_d["eligible_states_json"]) if c_d.get("eligible_states_json") else None
                    await upsert_catchment(
                        institution_id=inst_uuid, name=c_d["name"], eligible_states=eligible_states,
                        policy=c_d["policy"], details=c_d.get("details"),
                    )
        stats["catchment"] = len(catchments)
        
        srcs = conn.execute("SELECT * FROM kb_source_documents").fetchall()
        for s in srcs:
            s_d = row_to_dict(s)
            inst_row = conn.execute("SELECT name FROM kb_institutions WHERE id = ?", (s_d["institution_id"],)).fetchone()
            if inst_row:
                inst_uuid = inst_name_to_uuid.get(inst_row["name"])
                if inst_uuid:
                    await upsert_source_document(
                        institution_id=inst_uuid, url=s_d["url"], document_type=s_d.get("document_type", "webpage"),
                        title=s_d.get("title"), content_hash=s_d.get("content_hash"),
                        date_published=s_d.get("date_published"), confidence=s_d.get("confidence"),
                        academic_session=s_d.get("academic_session"), raw_content=s_d.get("raw_content"),
                    )
        stats["source_documents"] = len(srcs)
        
        conn.commit()
    finally:
        conn.close()
    
    return stats


def slugify(name: str) -> str:
    slug = name.lower().strip()
    for ch in " ,.-'/":
        slug = slug.replace(ch, "_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_")


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    
    async def test_imports():
        print("Testing imports...")
        from naija_admissions.institutions import ALL_INSTITUTIONS
        from naija_admissions.storage import _compute_hash
        from naija_admissions.utils import slugify as u_slugify
        print(f"Total institutions: {len(ALL_INSTITUTIONS)}")
        print(f"slugify test: {u_slugify('University of Lagos')}")
        print(f"hash test: {_compute_hash(b'test')[:16]}")
        print("All imports OK")
    
    asyncio.run(test_imports())