"""SQLite writer — 6 related tables + indexes."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ..models import Institution

_DDL = """
CREATE TABLE IF NOT EXISTS institutions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    short_name TEXT,
    institution_type TEXT NOT NULL,
    type TEXT NOT NULL,
    state TEXT,
    city TEXT,
    website TEXT,
    year_established INTEGER,
    catchment_policy TEXT,
    admission_requirements_json TEXT,
    application_process_json TEXT,
    confidence_json TEXT,
    last_updated TEXT
);

CREATE TABLE IF NOT EXISTS programs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    institution_id INTEGER NOT NULL,
    name TEXT,
    faculty TEXT,
    degree TEXT,
    level TEXT,
    duration_years INTEGER,
    affiliated_university TEXT,
    FOREIGN KEY (institution_id) REFERENCES institutions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS fees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    institution_id INTEGER NOT NULL,
    program_or_faculty TEXT,
    tuition_per_session_ngn INTEGER,
    tuition_per_session_usd INTEGER,
    currency TEXT,
    indigene_non_indigene_json TEXT,
    source_url TEXT,
    fee_year INTEGER,
    FOREIGN KEY (institution_id) REFERENCES institutions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS catchment_areas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    institution_id INTEGER NOT NULL,
    name TEXT,
    details TEXT,
    policy TEXT,
    FOREIGN KEY (institution_id) REFERENCES institutions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    institution_id INTEGER NOT NULL,
    url TEXT,
    provider TEXT,
    accessed_on TEXT,
    FOREIGN KEY (institution_id) REFERENCES institutions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS scrape_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT,
    ended_at TEXT,
    scraped INTEGER,
    failed INTEGER,
    paused INTEGER,
    credits_used INTEGER
);

CREATE INDEX IF NOT EXISTS idx_institutions_type ON institutions(institution_type);
CREATE INDEX IF NOT EXISTS idx_institutions_state ON institutions(state);
CREATE INDEX IF NOT EXISTS idx_institutions_name_type ON institutions(name, institution_type);
CREATE INDEX IF NOT EXISTS idx_programs_inst ON programs(institution_id);
CREATE INDEX IF NOT EXISTS idx_fees_inst ON fees(institution_id);
"""


def _connect(path: str | Path) -> sqlite3.Connection:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p)
    conn.executescript(_DDL)
    conn.commit()
    return conn


def _upsert_institution(conn: sqlite3.Connection, inst: Institution) -> int:
    name = inst.name
    req_json = json.dumps(inst.admission_requirements.model_dump(mode="json")) if inst.admission_requirements else None
    app_json = json.dumps(inst.application_process.model_dump(mode="json")) if inst.application_process else None
    conf_json = json.dumps(inst.confidence)
    cat_policy = None
    if inst.catchment_areas:
        first = inst.catchment_areas[0]
        cat_policy = first.policy.value if hasattr(first.policy, "value") else str(first.policy)
    cur = conn.execute(
        """INSERT INTO institutions
        (name, short_name, institution_type, type, state, city, website, year_established,
         catchment_policy, admission_requirements_json, application_process_json,
         confidence_json, last_updated)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(name) DO UPDATE SET
        short_name=excluded.short_name,
        institution_type=excluded.institution_type,
        type=excluded.type,
        state=excluded.state,
        city=excluded.city,
        website=excluded.website,
        year_established=excluded.year_established,
        catchment_policy=excluded.catchment_policy,
        admission_requirements_json=excluded.admission_requirements_json,
        application_process_json=excluded.application_process_json,
        confidence_json=excluded.confidence_json,
        last_updated=excluded.last_updated
        """,
        (
            name, inst.short_name,
            inst.institution_type.value if hasattr(inst.institution_type, "value") else str(inst.institution_type),
            inst.type.value if hasattr(inst.type, "value") else str(inst.type),
            inst.state, inst.city, inst.website, inst.year_established,
            cat_policy, req_json, app_json, conf_json, inst.last_updated,
        ),
    )
    conn.commit()
    rowid = cur.lastrowid
    if not rowid:
        row = conn.execute("SELECT id FROM institutions WHERE name = ?", (name,)).fetchone()
        rowid = row[0] if row else None
    return int(rowid) if rowid else 0


def _delete_dependents(conn: sqlite3.Connection, institution_id: int) -> None:
    for tbl in ("programs", "fees", "catchment_areas", "sources"):
        conn.execute(f"DELETE FROM {tbl} WHERE institution_id = ?", (institution_id,))


def write_institution(conn: sqlite3.Connection, inst: Institution) -> int:
    institution_id = _upsert_institution(conn, inst)
    if not institution_id:
        return 0
    _delete_dependents(conn, institution_id)
    for prog in inst.programs:
        conn.execute(
            """INSERT INTO programs (institution_id, name, faculty, degree, level,
            duration_years, affiliated_university) VALUES (?,?,?,?,?,?,?)""",
            (institution_id, prog.name, prog.faculty, prog.degree, prog.level,
             prog.duration_years, prog.affiliated_university),
        )
    for f in inst.fee_tiers:
        ind_json = json.dumps(f.indigene_vs_non_indigene) if f.indigene_vs_non_indigene else None
        conn.execute(
            """INSERT INTO fees (institution_id, program_or_faculty, tuition_per_session_ngn,
            tuition_per_session_usd, currency, indigene_non_indigene_json, source_url, fee_year)
            VALUES (?,?,?,?,?,?,?,?)""",
            (institution_id, f.program_or_faculty, f.tuition_per_session_ngn,
             f.tuition_per_session_usd, f.currency, ind_json, f.source_url, f.fee_year),
        )
    for c in inst.catchment_areas:
        conn.execute(
            "INSERT INTO catchment_areas (institution_id, name, details, policy) VALUES (?,?,?,?)",
            (institution_id, c.name, c.details,
             c.policy.value if hasattr(c.policy, "value") else str(c.policy)),
        )
    for s in inst.sources:
        conn.execute(
            "INSERT INTO sources (institution_id, url, provider, accessed_on) VALUES (?,?,?,?)",
            (institution_id, s.url, s.provider, s.accessed_on),
        )
    conn.commit()
    return institution_id


def record_scrape_run(
    conn: sqlite3.Connection,
    started_at: str,
    ended_at: str,
    scraped: int,
    failed: int,
    paused: bool,
    credits_used: int,
) -> None:
    conn.execute(
        """INSERT INTO scrape_runs (started_at, ended_at, scraped, failed, paused, credits_used)
        VALUES (?,?,?,?,?,?)""",
        (started_at, ended_at, scraped, failed, int(paused), credits_used),
    )
    conn.commit()


def write_sqlite(path: str | Path, institutions: list[Institution]) -> None:
    conn = _connect(path)
    try:
        for inst in institutions:
            write_institution(conn, inst)
    finally:
        conn.close()
