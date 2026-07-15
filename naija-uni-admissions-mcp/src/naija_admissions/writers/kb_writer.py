"""Idempotent writers for the 7-table knowledge-base schema.

All public functions are idempotent: re-running them with the same data
updates existing rows instead of duplicating. Returns the rowid (or 0 on
failure) so callers can chain writes.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime
from typing import Any


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _today() -> str:
    return datetime.utcnow().date().isoformat()


def _hash_content(text: str | None) -> str | None:
    if not text:
        return None
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def _json(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        try:
            json.loads(value)
            return value
        except (ValueError, TypeError):
            pass
    return json.dumps(value, ensure_ascii=False, default=str)


def upsert_institution_kb(
    conn: sqlite3.Connection,
    *,
    name: str,
    short_name: str | None = None,
    institution_type: str,
    ownership_type: str,
    state: str | None = None,
    city: str | None = None,
    website: str | None = None,
    admission_portal: str | None = None,
    year_established: int | None = None,
    last_updated: str | None = None,
) -> int:
    last_updated = last_updated or _now_iso()
    conn.execute(
        """
        INSERT INTO kb_institutions
            (name, short_name, institution_type, ownership_type, state, city,
             website, admission_portal, year_established, last_updated)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(name) DO UPDATE SET
            short_name=excluded.short_name,
            institution_type=excluded.institution_type,
            ownership_type=excluded.ownership_type,
            state=excluded.state,
            city=excluded.city,
            website=excluded.website,
            admission_portal=excluded.admission_portal,
            year_established=excluded.year_established,
            last_updated=excluded.last_updated
        """,
        (
            name, short_name, institution_type, ownership_type, state, city,
            website, admission_portal, year_established, last_updated,
        ),
    )
    conn.commit()
    row = conn.execute("SELECT id FROM kb_institutions WHERE name = ?", (name,)).fetchone()
    return int(row[0]) if row else 0


def upsert_faculty_kb(
    conn: sqlite3.Connection,
    *,
    institution_id: int,
    name: str,
) -> int:
    conn.execute(
        """
        INSERT INTO kb_faculties (institution_id, name)
        VALUES (?,?)
        ON CONFLICT(institution_id, name) DO NOTHING
        """,
        (institution_id, name),
    )
    conn.commit()
    row = conn.execute(
        "SELECT id FROM kb_faculties WHERE institution_id = ? AND name = ?",
        (institution_id, name),
    ).fetchone()
    return int(row[0]) if row else 0


def upsert_program_kb(
    conn: sqlite3.Connection,
    *,
    institution_id: int,
    name: str,
    faculty_id: int | None = None,
    degree: str | None = None,
    level: str | None = None,
    duration_years: int | None = None,
    affiliated_university: str | None = None,
) -> int:
    conn.execute(
        """
        INSERT INTO kb_programs
            (institution_id, faculty_id, name, degree, level, duration_years, affiliated_university)
        VALUES (?,?,?,?,?,?,?)
        ON CONFLICT(institution_id, name) DO UPDATE SET
            faculty_id=excluded.faculty_id,
            degree=excluded.degree,
            level=excluded.level,
            duration_years=excluded.duration_years,
            affiliated_university=excluded.affiliated_university
        """,
        (institution_id, faculty_id, name, degree, level, duration_years, affiliated_university),
    )
    conn.commit()
    row = conn.execute(
        "SELECT id FROM kb_programs WHERE institution_id = ? AND name = ?",
        (institution_id, name),
    ).fetchone()
    return int(row[0]) if row else 0


def upsert_admission_requirements_kb(
    conn: sqlite3.Connection,
    *,
    institution_id: int,
    program_id: int | None = None,
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
) -> int:
    awaiting = (
        int(awaiting_result_accepted) if awaiting_result_accepted is not None else None
    )
    post_utme = int(post_utme_required) if post_utme_required is not None else None
    existing = conn.execute(
        "SELECT id FROM kb_admission_requirements "
        "WHERE institution_id = ? AND COALESCE(program_id, -1) = COALESCE(?, -1)",
        (institution_id, program_id),
    ).fetchone()
    if existing:
        conn.execute(
            """
            UPDATE kb_admission_requirements SET
                olevel_subjects_json = ?,
                olevel_credits_min = ?,
                utme_subjects_json = ?,
                minimum_jamb = ?,
                minimum_credits = ?,
                awaiting_result_accepted = ?,
                max_olevel_sittings = ?,
                direct_entry_requirements = ?,
                post_utme_required = ?,
                post_utme_format = ?,
                post_utme_weight_pct = ?,
                aggregate_formula = ?
            WHERE id = ?
            """,
            (
                _json(olevel_subjects), olevel_credits_min,
                _json(utme_subjects), minimum_jamb, minimum_credits,
                awaiting, max_olevel_sittings,
                direct_entry_requirements, post_utme, post_utme_format,
                post_utme_weight_pct, aggregate_formula,
                existing[0],
            ),
        )
        conn.commit()
        return int(existing[0])
    cur = conn.execute(
        """
        INSERT INTO kb_admission_requirements
            (institution_id, program_id, olevel_subjects_json, olevel_credits_min,
             utme_subjects_json, minimum_jamb, minimum_credits,
             awaiting_result_accepted, max_olevel_sittings,
             direct_entry_requirements, post_utme_required, post_utme_format,
             post_utme_weight_pct, aggregate_formula)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            institution_id, program_id, _json(olevel_subjects), olevel_credits_min,
            _json(utme_subjects), minimum_jamb, minimum_credits,
            awaiting, max_olevel_sittings,
            direct_entry_requirements, post_utme, post_utme_format,
            post_utme_weight_pct, aggregate_formula,
        ),
    )
    conn.commit()
    return int(cur.lastrowid or 0)


def upsert_cutoff_kb(
    conn: sqlite3.Connection,
    *,
    institution_id: int,
    academic_year: str,
    program_id: int | None = None,
    merit_cutoff: float | None = None,
    departmental_cutoff: float | None = None,
    catchment_cutoff: float | None = None,
    elds_cutoff: float | None = None,
    aggregate_formula: str | None = None,
    source_url: str | None = None,
    crawl_date: str | None = None,
) -> int:
    crawl_date = crawl_date or _today()
    conn.execute(
        """
        INSERT INTO kb_cutoff_marks
            (institution_id, program_id, academic_year, merit_cutoff, departmental_cutoff,
             catchment_cutoff, elds_cutoff, aggregate_formula, source_url, crawl_date)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(institution_id, program_id, academic_year) DO UPDATE SET
            merit_cutoff=excluded.merit_cutoff,
            departmental_cutoff=excluded.departmental_cutoff,
            catchment_cutoff=excluded.catchment_cutoff,
            elds_cutoff=excluded.elds_cutoff,
            aggregate_formula=excluded.aggregate_formula,
            source_url=excluded.source_url,
            crawl_date=excluded.crawl_date
        """,
        (
            institution_id, program_id, academic_year, merit_cutoff, departmental_cutoff,
            catchment_cutoff, elds_cutoff, aggregate_formula, source_url, crawl_date,
        ),
    )
    conn.commit()
    row = conn.execute(
        "SELECT id FROM kb_cutoff_marks WHERE institution_id = ? AND "
        "COALESCE(program_id, -1) = COALESCE(?, -1) AND academic_year = ?",
        (institution_id, program_id, academic_year),
    ).fetchone()
    return int(row[0]) if row else 0


def upsert_catchment_area_kb(
    conn: sqlite3.Connection,
    *,
    institution_id: int,
    name: str,
    policy: str,
    eligible_states: list[str] | None = None,
    details: str | None = None,
) -> int:
    conn.execute(
        """
        INSERT INTO kb_catchment_areas
            (institution_id, name, eligible_states_json, policy, details)
        VALUES (?,?,?,?,?)
        ON CONFLICT(institution_id, name, policy) DO UPDATE SET
            eligible_states_json=excluded.eligible_states_json,
            details=excluded.details
        """,
        (institution_id, name, _json(eligible_states), policy, details),
    )
    conn.commit()
    row = conn.execute(
        "SELECT id FROM kb_catchment_areas WHERE institution_id = ? AND name = ? AND policy = ?",
        (institution_id, name, policy),
    ).fetchone()
    return int(row[0]) if row else 0


def upsert_source_document_kb(
    conn: sqlite3.Connection,
    *,
    institution_id: int,
    url: str,
    crawl_date: str | None = None,
    date_published: str | None = None,
    document_type: str | None = None,
    confidence: str | None = None,
    academic_session: str | None = None,
    raw_content: str | None = None,
) -> int:
    crawl_date = crawl_date or _today()
    content_hash = _hash_content(raw_content)
    conn.execute(
        """
        INSERT INTO kb_source_documents
            (institution_id, url, crawl_date, date_published, document_type,
             confidence, academic_session, content_hash, raw_content)
        VALUES (?,?,?,?,?,?,?,?,?)
        ON CONFLICT(institution_id, url, crawl_date) DO UPDATE SET
            date_published=excluded.date_published,
            document_type=excluded.document_type,
            confidence=excluded.confidence,
            academic_session=excluded.academic_session,
            content_hash=excluded.content_hash,
            raw_content=excluded.raw_content
        """,
        (
            institution_id, url, crawl_date, date_published, document_type,
            confidence, academic_session, content_hash, raw_content,
        ),
    )
    conn.commit()
    row = conn.execute(
        "SELECT id FROM kb_source_documents WHERE institution_id = ? AND url = ? AND crawl_date = ?",
        (institution_id, url, crawl_date),
    ).fetchone()
    return int(row[0]) if row else 0


def has_content_changed(
    conn: sqlite3.Connection,
    *,
    institution_id: int,
    url: str,
    new_content: str,
) -> bool:
    new_hash = _hash_content(new_content)
    row = conn.execute(
        "SELECT content_hash FROM kb_source_documents "
        "WHERE institution_id = ? AND url = ? "
        "ORDER BY crawl_date DESC LIMIT 1",
        (institution_id, url),
    ).fetchone()
    if not row or not row[0]:
        return True
    return row[0] != new_hash
