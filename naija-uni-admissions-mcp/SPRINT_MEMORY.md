# CKAP Sprint Memory — crawl-1
Created: 2026-07-31 | Branch: crawl-1 | Project: campus-crawler / naija-uni-admissions-mcp

## What Has Been Built (Audit — 28 files, ~85% complete)

### Core Pipeline
- Crawl4AI + Playwright + DuckDuckGo (crawl4ai_client.py) — full with throttling, retries, rate-limit detection
- 4 regex parsers: requirements, fees, catchment, programs (parsers/)
- AI extraction module (ai_extractor.py + extraction_models.py) — complete but DISABLED (`AI_EXTRACTION_ENABLED = False`)
- Pipeline orchestrator (scraper.py) — complete
- MCP stdio server (server.py) — complete
- Resume + budget control (resume.py, budget.py) — complete
- Discovery (discovery.py) — NUC/NCCE/NMCN done; NBTE + JAMB are STUBS
- Website mapper (website_mapper.py) — complete
- Eligibility engine (eligibility.py) — complete

### Data & Writers
- 314 institution seeds (institutions.py) — data quality issues: 50+ malformed URLs, undercount vs README claim (~580)
- 3 local writers: JSON, CSV, SQLite (writers/)
- 7-table normalized KB writer (kb_writer.py + kb_schema.py)
- Pydantic models (models.py)
- Storage module (storage.py) — complete but UNUSED in pipeline

### Supabase (3 writer modules — must consolidate)
- `supabase_schema.sql`: 24 tables (22 production + 2 staging) + 8 enums + RLS + triggers + functions — idempotent, 9KB
- `supabase_ops.py`: CANONICAL writer — 22 production upserts + staging + migration + `upsert_full_institution()` (but only 9 of 22 upserts actually called inside it)
- `supabase_client.py` + `supabase_writer.py`: DEAD CODE (obsolete table names, `run_with_retry` coroutine-reuse bug)

### Tests (~80 unit tests across 6 modules)
- test_parsers.py, test_extraction_models.py, test_prompts.py, test_website_mapper.py, test_ai_extractor.py, test_scraper.py + conftest.py
- `test_full_pipeline.py`: E2E script exists, unrun

### Key Files Not Modified
- `supabase_schema.sql` (859 lines, full schema)
- `.env` (Supabase keys, NVIDIA API key, S3 config)

---

## What Remains — Sprint Breakdown

### Sprint A: Schema & Storage (1 day)
- Apply full `supabase_schema.sql` in Supabase SQL Editor
- Create Storage buckets (`crawl-assets`, `institution-assets`)
- Wire `storage.store_crawl_artifacts()` into scraper
- Verify RLS + triggers

### Sprint B: Code Cleanup (0.5 day)
- Delete `supabase_client.py` + `supabase_writer.py`
- Delete `tenacity` dependency (unused)
- Consolidate `slugify` (3 files)
- Single ELDS source (4 files)

### Sprint C: AI Enablement (1 day)
- Validate NVIDIA API key
- Flip `AI_EXTRACTION_ENABLED = True`
- Fix `content: None` null-guard in `ai_extractor.py`
- Fix dead `scraper.py:457–462` block
- Wire remaining 13 upserts in `upsert_full_institution()`

### Sprint D: Seed Data Quality (1 day)
- Re-run discovery (current 314 vs target ~580)
- Implement NBTEConnector + JAMBConnector
- Clean 50+ malformed URLs + state casing

### Sprint E: Reliability (1 day)
- Atomic write for `resume.state_save`
- File locking for `state.json`
- Retry `httpx.ConnectError` / `ReadError`
- Circuit breaker for DDG rate-limit

### Sprint F: Validation (0.5 day)
- `pytest` (all ~80)
- `test_full_pipeline.py --no-upsert` E2E
- `test_full_pipeline.py` with Supabase enabled

### Sprint G: Ops & Deploy (1–2 days)
- CI/CD (ruff + mypy + pytest)
- Metrics counters
- `--dry-run` flag
- Production deployment target
- Update `pyproject.toml` description (Firecrawl → Crawl4AI)
- Update README + CHANGELOG.md

---

## Critical Bugs Found (Not Yet Fixed)
1. `fees_parser.py:105` — year extraction: both branches identical
2. `scraper.py:457–462` — broken `and`/`or` precedence + `pass` body
3. `ai_extractor.py` — `content` can be `None` (no null-guard)
4. `supabase_client.py` + `supabase_writer.py` — `run_with_retry` reuses already-awaited coroutine
5. `AI_EXTRACTION_ENABLED = False` — regex-only mode in production

---

## Environment / Keys (in `.env`, not committed)
- NVIDIA NIM API key: `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`
- Supabase: `fhqylwughhlxumgpsvho` | `https://fhqylwughhlxumgpsvho.supabase.co`
- S3 endpoint: `https://fhqylwughhlxumgpsvho.storage.supabase.co/storage/v1/s3` (region `eu-west-1`)
- Model name in `.env`: `nvidia/nemotron-3-ultra-550b-a55b`

---

## Quick Wins (do in order)
1. Apply `supabase_schema.sql` → Supabase SQL Editor
2. `pytest`
3. Delete dead `supabase_client.py` + `supabase_writer.py`
4. Fix `fees_parser.py:105`
5. Run `test_full_pipeline.py --no-upsert`

---

## Next Action
Run the full schema in Supabase SQL Editor (copy from `supabase_schema.sql`), then run `pytest`.
