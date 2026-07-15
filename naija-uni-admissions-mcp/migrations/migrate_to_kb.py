"""One-shot migration: populates the KB schema from existing JSON data files.

Sources:
    data/institutions.json  —  pilot scrape (9 institutions)
    data/ui_admissions_2025_2026.json — hand-crafted University of Ibadan record(s)

Run this ONCE. It is idempotent (re-running safely updates, not duplicates).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
DB_PATH = DATA_DIR / "institutions.db"

sys.path.insert(0, str(PROJECT_DIR / "src"))

from naija_admissions.writers.kb_schema import connect_kb
from naija_admissions.writers.kb_writer import (
    upsert_admission_requirements_kb,
    upsert_catchment_area_kb,
    upsert_cutoff_kb,
    upsert_faculty_kb,
    upsert_institution_kb,
    upsert_program_kb,
    upsert_source_document_kb,
)

_ELDS_STATES = [
    "Adamawa", "Bauchi", "Bayelsa", "Benue", "Borno", "Cross River", "Gombe", "Jigawa",
    "Kaduna", "Kano", "Katsina", "Kebbi", "Kogi", "Kwara", "Nasarawa", "Niger", "Plateau",
    "Rivers", "Sokoto", "Taraba", "Yobe", "Zamfara",
]
_CATCHMENT_POLICY = [("ELDS", "ELDS", "geographical", _ELDS_STATES, "Educationally Less Developed States (JAMB default)")]


def _institution_type(raw: str) -> str:
    return raw.lower() if raw else "university"


def _ownership_type(raw: str) -> str:
    return raw.lower() if raw else "federal"


def _migrate_pilot_institutions(conn) -> list[dict]:
    path = DATA_DIR / "institutions.json"
    if not path.exists():
        print(f"  SKIP: {path.name} not found")
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    migrated: list[dict] = []
    print(f"  Processing {len(data)} institutions from {path.name}...")
    for inst in data:
        name = inst.get("name")
        if not name:
            continue
        inst_id = upsert_institution_kb(
            conn,
            name=name,
            short_name=inst.get("short_name"),
            institution_type=_institution_type(inst.get("institution_type")),
            ownership_type=_ownership_type(inst.get("type")),
            state=inst.get("state"),
            city=inst.get("city"),
            website=inst.get("website"),
            admission_portal=inst.get("admission_portal") or _portal_from_sources(inst.get("sources", [])),
            year_established=inst.get("year_established"),
            last_updated=inst.get("last_updated"),
        )
        _migrate_common_fields(conn, inst_id, inst)
        migrated.append({"name": name, "inst_id": inst_id})
        print(f"    + {name} (id={inst_id})")
    return migrated


def _migrate_ui_record(conn) -> list[dict]:
    path = DATA_DIR / "ui_admissions_2025_2026.json"
    if not path.exists():
        print(f"  SKIP: {path.name} not found")
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        records = data
    else:
        records = [data]
    migrated: list[dict] = []
    print(f"  Processing {len(records)} records from {path.name}...")
    for inst in records:
        name = inst.get("name")
        if not name:
            continue
        inst_id = upsert_institution_kb(
            conn,
            name=name,
            short_name=inst.get("short_name"),
            institution_type=_institution_type(inst.get("institution_type")),
            ownership_type=_ownership_type(inst.get("type")),
            state=inst.get("state"),
            city=inst.get("city"),
            website=inst.get("website"),
            admission_portal=inst.get("admission_portal") or _app_portal(inst),
            year_established=inst.get("year_established"),
            last_updated=inst.get("last_updated"),
        )
        _migrate_common_fields(conn, inst_id, inst)
        _migrate_cutoffs_from_json(conn, inst_id, inst)
        migrated.append({"name": name, "inst_id": inst_id})
        print(f"    + {name} (id={inst_id})")
    return migrated


def _migrate_common_fields(conn, inst_id: int, inst: dict) -> None:
    faculties = inst.get("faculties") or []
    for fname in faculties:
        uid = upsert_faculty_kb(conn, institution_id=inst_id, name=str(fname))
        if uid:
            _maybe_migrate_faculty_defaults(conn, inst_id, uid, str(fname))

    programs = inst.get("programs") or []
    for prog in programs:
        if not isinstance(prog, dict):
            continue
        prog_name = prog.get("name", "")
        if not prog_name:
            continue
        fac_id = None
        for fname in faculties:
            if str(fname).lower() in prog_name.lower():
                row = conn.execute(
                    "SELECT id FROM kb_faculties WHERE institution_id = ? AND name = ?",
                    (inst_id, str(fname)),
                ).fetchone()
                if row:
                    fac_id = row[0]
                break
        upsert_program_kb(
            conn,
            institution_id=inst_id,
            name=prog_name,
            faculty_id=fac_id,
            degree=prog.get("degree"),
            level=prog.get("level"),
            duration_years=prog.get("duration_years"),
            affiliated_university=prog.get("affiliated_university"),
        )

    req = inst.get("admission_requirements")
    if req and isinstance(req, dict):
        post = req.get("post_utme") or {}
        upsert_admission_requirements_kb(
            conn,
            institution_id=inst_id,
            program_id=None,
            olevel_subjects=req.get("olevel_subjects"),
            olevel_credits_min=req.get("olevel_credits_min"),
            utme_subjects=req.get("utme_subjects"),
            minimum_jamb=req.get("utme_cutoff_general"),
            minimum_credits=req.get("olevel_credits_min"),
            direct_entry_requirements=req.get("direct_entry_requirements"),
            post_utme_required=post.get("required"),
            post_utme_format=post.get("format"),
            post_utme_weight_pct=post.get("weight_pct"),
            aggregate_formula=post.get("format"),
        )

    for (name, pol_id, policy, states, details) in _CATCHMENT_POLICY:
        upsert_catchment_area_kb(
            conn,
            institution_id=inst_id,
            name=name,
            policy=policy,
            eligible_states=states,
            details=details,
        )

    app = inst.get("application_process") or {}
    steps = app.get("steps") or []
    steps_text = "\n".join(steps) if steps else None

    sources = inst.get("sources") or []
    for s in sources:
        if not isinstance(s, dict):
            continue
        upsert_source_document_kb(
            conn,
            institution_id=inst_id,
            url=s.get("url", ""),
            crawl_date=s.get("accessed_on"),
            date_published=s.get("date_published"),
            document_type=s.get("document_type") or s.get("provider"),
            confidence=_flatten_confidence(s.get("confidence") or inst.get("confidence")),
            academic_session=s.get("academic_session") or "2025/2026",
            raw_content=steps_text,
        )


def _migrate_cutoffs_from_json(conn, inst_id: int, inst: dict) -> None:
    cutoffs = inst.get("cutoffs_2025_2026")
    if not cutoffs:
        return
    for c in cutoffs:
        prog_name = c.get("programme", "")
        if not prog_name:
            continue
        row = conn.execute(
            "SELECT id FROM kb_programs WHERE institution_id = ? AND name = ?",
            (inst_id, prog_name),
        ).fetchone()
        prog_id = int(row[0]) if row else None
        upsert_cutoff_kb(
            conn,
            institution_id=inst_id,
            academic_year="2025/2026",
            program_id=prog_id,
            merit_cutoff=c.get("merit"),
            catchment_cutoff=c.get("catchment"),
            elds_cutoff=c.get("elds"),
            aggregate_formula=inst.get("aggregate_formula"),
            source_url=str(c.get("source_url") or ""),
            crawl_date=datetime.utcnow().date().isoformat(),
        )


def _portal_from_sources(sources: list) -> str | None:
    for s in sources:
        url = s.get("url", "") if isinstance(s, dict) else str(s)
        if "admission" in url.lower() or "application" in url.lower():
            return url
    return sources[0].get("url") if sources else None


def _app_portal(inst: dict) -> str | None:
    app = inst.get("application_process") or {}
    return app.get("portal_url") or None


def _flatten_confidence(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return json.dumps(value, default=str)
    return str(value)


def _maybe_migrate_faculty_defaults(conn, inst_id: int, fac_id: int, fname: str) -> None:
    row = conn.execute(
        "SELECT id FROM kb_admission_requirements WHERE institution_id = ? AND program_id IS NULL",
        (inst_id,),
    ).fetchone()
    if row:
        return
    upsert_admission_requirements_kb(
        conn,
        institution_id=inst_id,
        program_id=None,
        minimum_jamb=200,
    )


def _dedupe_null_program_requirements(conn) -> None:
    rows = conn.execute(
        """
        SELECT institution_id, id
        FROM kb_admission_requirements
        WHERE program_id IS NULL
        ORDER BY institution_id, id
        """
    ).fetchall()
    seen: dict[Any, int] = {}
    to_delete: list[int] = []
    for inst_id, req_id in rows:
        if inst_id in seen:
            to_delete.append(req_id)
        else:
            seen[inst_id] = req_id
    if to_delete:
        placeholders = ",".join("?" * len(to_delete))
        conn.execute(
            f"DELETE FROM kb_admission_requirements WHERE id IN ({placeholders})",
            to_delete,
        )
        print(f"  Removed {len(to_delete)} duplicate NULL-program requirement rows")


def main() -> None:
    conn = connect_kb(DB_PATH)
    try:
        print("=== Migrating pilot scrape data ===")
        _migrate_pilot_institutions(conn)
        print("\n=== Migrating University of Ibadan data ===")
        _migrate_ui_record(conn)
        print("\n=== Cleaning up duplicate NULL-program requirement rows ===")
        _dedupe_null_program_requirements(conn)
        conn.commit()
        stats = {}
        for tbl in (
            "kb_institutions", "kb_faculties", "kb_programs",
            "kb_admission_requirements", "kb_cutoff_marks",
            "kb_catchment_areas", "kb_source_documents",
        ):
            cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            stats[tbl] = cnt
            print(f"  {tbl}: {cnt} rows")
        print(f"\nMigration complete. DB: {DB_PATH}")
        print(f"Integrity: {conn.execute('PRAGMA integrity_check').fetchone()[0]}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()