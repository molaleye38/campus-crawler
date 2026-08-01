"""Knowledge-base schema — 7 normalized tables for Campus Compass.

Tables:
    institutions         — one row per school
    faculties            — one row per faculty within an institution
    programs             — one row per course/department
    admission_requirements — institution-level OR program-level requirements
    cutoff_marks          — per-program, per-year cut-offs (merit/catchment/elds)
    catchment_areas       — policy + eligible states per institution
    source_documents      — crawl history with content_hash for change detection

Coexists with the legacy 6-table schema in sqlite_writer.py. New code should
use these tables; legacy `write_institution()` is untouched.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

_KB_DDL = """
CREATE TABLE IF NOT EXISTS kb_institutions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    short_name TEXT,
    institution_type TEXT NOT NULL,
    ownership_type TEXT NOT NULL,
    state TEXT,
    city TEXT,
    website TEXT,
    admission_portal TEXT,
    year_established INTEGER,
    last_updated TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS kb_faculties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    institution_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    UNIQUE(institution_id, name),
    FOREIGN KEY (institution_id) REFERENCES kb_institutions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS kb_programs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    institution_id INTEGER NOT NULL,
    faculty_id INTEGER,
    name TEXT NOT NULL,
    degree TEXT,
    level TEXT,
    duration_years INTEGER,
    affiliated_university TEXT,
    UNIQUE(institution_id, name),
    FOREIGN KEY (institution_id) REFERENCES kb_institutions(id) ON DELETE CASCADE,
    FOREIGN KEY (faculty_id) REFERENCES kb_faculties(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS kb_admission_requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    institution_id INTEGER NOT NULL,
    program_id INTEGER,
    olevel_subjects_json TEXT,
    olevel_credits_min INTEGER,
    utme_subjects_json TEXT,
    minimum_jamb INTEGER,
    minimum_credits INTEGER,
    awaiting_result_accepted INTEGER,
    max_olevel_sittings INTEGER,
    direct_entry_requirements TEXT,
    post_utme_required INTEGER,
    post_utme_format TEXT,
    post_utme_weight_pct INTEGER,
    aggregate_formula TEXT,
    UNIQUE(institution_id, program_id),
    FOREIGN KEY (institution_id) REFERENCES kb_institutions(id) ON DELETE CASCADE,
    FOREIGN KEY (program_id) REFERENCES kb_programs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS kb_cutoff_marks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    institution_id INTEGER NOT NULL,
    program_id INTEGER,
    academic_year TEXT NOT NULL,
    merit_cutoff REAL,
    departmental_cutoff REAL,
    catchment_cutoff REAL,
    elds_cutoff REAL,
    aggregate_formula TEXT,
    source_url TEXT,
    crawl_date TEXT,
    UNIQUE(institution_id, program_id, academic_year),
    FOREIGN KEY (institution_id) REFERENCES kb_institutions(id) ON DELETE CASCADE,
    FOREIGN KEY (program_id) REFERENCES kb_programs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS kb_catchment_areas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    institution_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    eligible_states_json TEXT,
    policy TEXT NOT NULL,
    details TEXT,
    UNIQUE(institution_id, name, policy),
    FOREIGN KEY (institution_id) REFERENCES kb_institutions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS kb_source_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    institution_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    crawl_date TEXT NOT NULL,
    date_published TEXT,
    document_type TEXT,
    confidence TEXT,
    academic_session TEXT,
    content_hash TEXT,
    raw_content TEXT,
    UNIQUE(institution_id, url, crawl_date),
    FOREIGN KEY (institution_id) REFERENCES kb_institutions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_kb_inst_type ON kb_institutions(institution_type);
CREATE INDEX IF NOT EXISTS idx_kb_inst_state ON kb_institutions(state);
CREATE INDEX IF NOT EXISTS idx_kb_inst_name ON kb_institutions(name);
CREATE INDEX IF NOT EXISTS idx_kb_fac_inst ON kb_faculties(institution_id);
CREATE INDEX IF NOT EXISTS idx_kb_prog_inst ON kb_programs(institution_id);
CREATE INDEX IF NOT EXISTS idx_kb_prog_fac ON kb_programs(faculty_id);
CREATE INDEX IF NOT EXISTS idx_kb_prog_name ON kb_programs(name);
CREATE INDEX IF NOT EXISTS idx_kb_req_inst ON kb_admission_requirements(institution_id);
CREATE INDEX IF NOT EXISTS idx_kb_req_prog ON kb_admission_requirements(program_id);
CREATE INDEX IF NOT EXISTS idx_kb_cut_inst ON kb_cutoff_marks(institution_id);
CREATE INDEX IF NOT EXISTS idx_kb_cut_prog ON kb_cutoff_marks(program_id);
CREATE INDEX IF NOT EXISTS idx_kb_cut_year ON kb_cutoff_marks(academic_year);
CREATE INDEX IF NOT EXISTS idx_kb_cat_inst ON kb_catchment_areas(institution_id);
CREATE INDEX IF NOT EXISTS idx_kb_src_inst ON kb_source_documents(institution_id);
CREATE INDEX IF NOT EXISTS idx_kb_src_hash ON kb_source_documents(content_hash);
"""


def connect_kb(path: str | Path) -> sqlite3.Connection:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(_KB_DDL)
    conn.commit()
    return conn


def drop_kb_tables(conn: sqlite3.Connection) -> None:
    for tbl in (
        "kb_source_documents",
        "kb_catchment_areas",
        "kb_cutoff_marks",
        "kb_admission_requirements",
        "kb_programs",
        "kb_faculties",
        "kb_institutions",
    ):
        conn.execute(f"DROP TABLE IF EXISTS {tbl}")
    conn.commit()
