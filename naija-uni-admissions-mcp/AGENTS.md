# AGENTS.md

Notes for AI coding agents working in this repo.

## Stack
- Python 3.11+
- MCP (Model Context Protocol) server
- Crawl4AI (local scraping via Playwright/Chromium) for page rendering
- DuckDuckGo HTML endpoint via httpx for search (no API key)
- Pydantic v2 for data models
- Supabase (PostgreSQL) for production knowledge base
- Outputs: JSON + CSV + SQLite (local) + Supabase (production)

## Environment
Optional env vars (see `.env.example`):
- `NGN_PER_USD` (default 1600) — used by `parsers/fees_parser.py` to convert NGN tuition to USD
- `MAX_PAGES_PER_RUN` (default 0 = unlimited) — cap pages scraped in a single invocation
- `SUPABASE_URL` — Supabase project URL
- `SUPABASE_ANON_KEY` — Supabase anon key (for read access)
- `SUPABASE_SERVICE_ROLE_KEY` — Supabase service role key (for write access, crawler)

Load with `python-dotenv` (already a dependency).

## Commands
```bash
# Install (creates a venv automatically)
uv sync

# One-time: install Playwright Chromium browser
uv run python -m playwright install chromium

# Run the MCP server (used by opencode / any MCP client)
uv run python -m naija_admissions.server

# Lint
uv run ruff check src

# Type check
uv run mypy src

# Tests
uv run pytest

# Run full pipeline test (crawl + upsert to Supabase)
uv run python test_full_pipeline.py
```

## Project layout
```
src/naija_admissions/
├── server.py              (MCP entry — registered tool: run_admissions_scrape)
├── models.py              (InstitutionType enum + pydantic schema)
├── institutions.py        (seed lists: ~270 unis + ~150 polys + ~163 COEs)
├── crawl4ai_client.py     (DuckDuckGo search + Crawl4AI scrape via Playwright)
├── budget.py              (page counter + optional MAX_PAGES_PER_RUN cap)
├── resume.py              (state.json load/save/lock)
├── utils.py               (polite_delay, NGN->USD, structlog setup)
├── scraper.py             (per-institution pipeline orchestration)
├── normalizer.py          (dedupe sources, unify name spellings)
├── supabase_ops.py        (single canonical Supabase writer — replaces old supabase_client.py + supabase_writer.py)
├── storage.py             (Supabase Storage via boto3 S3 — bucket setup, upload, presigned URLs)
├── parsers/
│   ├── requirements_parser.py  (type-aware UTME cutoff ranges)
│   ├── fees_parser.py          (NGN->USD conversion)
│   ├── catchment_parser.py     (universities only; poly/COE = none)
│   └── programs_parser.py      (recognizes ND|HND|NCE|B.Sc|B.A|B.Eng|MBBS|LL.B)
└── writers/
    ├── json_writer.py
    ├── csv_writer.py
    └── sqlite_writer.py         (6 tables: institutions, programs, fees, catchment_areas, sources, scrape_runs)
```

## Knowledge Base Schema (Supabase)

Production tables:
- `institutions` — one row per school
- `faculties` — faculties within institutions
- `programs` — courses/departments
- `admission_requirements` — institution or program-level requirements
- `olevel_rules` — O-Level subject rules
- `utme_rules` — UTME subject rules
- `postutme_rules` — Post-UTME rules
- `departmental_cutoffs` — per-program, per-session cutoffs (merit/catchment/ELDS)
- `catchment` — catchment areas with eligible states
- `source_documents` — provenance tracking
- `crawl_logs` — audit trail of every crawl

Staging layer:
- `raw_crawl_data` — raw extracted data pending validation
- `validated_data` — approved data ready for promotion

## Conventions
- No comments in Python files unless absolutely needed — code should be self-documenting
- Async-first; every I/O function is `async def`
- Pydantic models live in `models.py`, parsers mutate them
- All scrapes go through `crawl4ai_client.py` (no direct httpx/Crawl4AI calls elsewhere)
- `state.json` is the single source of truth for resume tracking
- No API key gate — Crawl4AI runs locally

## Supabase Integration Flow
1. Crawler extracts data → builds `Institution` Pydantic model
2. After successful crawl, `supabase_ops.upsert_full_institution()` upserts to:
   - `institutions`, `faculties`, `departments`, `courses`
   - `admission_requirements`, `departmental_cutoffs`, `catchment`
   - `fees`, `deadlines`, `source_documents`, `crawl_logs`
3. Crawl artifacts (HTML/markdown/PDF/screenshots) uploaded to Supabase Storage via `storage.store_crawl_artifacts()`
4. Raw extracted data also stored in `raw_crawl_data` for review
5. On approval, `validated_data` promoted to production tables
6. Campus Compass app reads directly from production tables

## Supabase client usage

Only `supabase_ops.py` (the canonical writer) is used. The old `supabase_client.py` and `supabase_writer.py` were removed in Sprint B. Uses the **async** Supabase client (`supabase._async.client.AsyncClient`). Every I/O function is `async def` and must be awaited.

```python
from naija_admissions.supabase_ops import (
    get_client,                  # async — `await get_client(use_service_role=True)`
    upsert_institution,          # async — single institution upsert
    upsert_faculty,              # async
    upsert_course,               # async
    upsert_admission_requirements,  # async
    upsert_fees,                 # async
    upsert_deadline,             # async
    upsert_departmental_cutoff,  # async
    upsert_catchment,            # async
    upsert_source_document,      # async
    log_crawl,                   # async
    upsert_full_institution,     # async — high-level: takes a payload dict
    stage_raw_crawl,             # async — staging
    promote_to_validated,        # async — promote after review
)
```

Common gotchas:
- `get_client()` is async — do `await get_client(use_service_role=True)`
- `.table(...).execute()` returns a coroutine — always `await` it before reading `.data`
- `log_crawl(institution_id, url, status, ...)` — institution_id first, then url/status
- `upsert_full_institution(payload)` expects a dict with keys: `institution`, `faculties`, `programs`, `admission_requirements`, `fees`, `deadlines`, `catchment`, `cutoffs`

## Schema idempotency

`supabase_schema.sql` is safe to re-run. It uses:
- `do $$ ... exception when duplicate_object` blocks for enums
- `drop policy if exists` before each `create policy`
- `drop trigger if exists` before the trigger
- `create table if not exists` and indexes for everything else

Re-paste anytime to apply schema updates without errors.

## Testing notes for future sessions
- Unit tests live in `tests/` (not yet scaffolded — add when first parser is built)
- Parser tests use sample markdown fixtures under `tests/fixtures/`
- Crawl4AI requires Playwright Chromium installed (`playwright install chromium`)
- Pilot verification (9 institutions, 3 of each type) is the integration test
