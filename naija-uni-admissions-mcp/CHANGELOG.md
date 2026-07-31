# CHANGELOG

## [Unreleased] — Sprint A→G (2026-07-31)

### Changed
- **Migration**: Firecrawl → Crawl4AI (Playwright/Chromium) for page rendering; DuckDuckGo HTML endpoint for search (no API key required).
- **Schema unification**: From 11-table flat schema to 22-table normalized schema in Supabase (institutions, faculties, departments, courses, course_aliases, subjects, subject_aliases, admission_requirements, olevel_requirements, utme_requirements, direct_entry, post_utme, aggregate_formulas, departmental_cutoffs, catchment, elds, fees, deadlines, admission_news, source_documents, crawl_logs, knowledge_versions).
- **Staging layer**: Added raw_crawl_data + validated_data for review workflow.
- **Knowledge versioning**: Auto-versioning triggers on institutions, courses, departmental_cutoffs, admission_requirements, fees, deadlines.
- **pyproject.toml description**: Updated from "via Firecrawl" to "via Crawl4AI and store in Supabase".

### Removed
- `tenacity` (unused; custom retry logic in `run_with_retry`).
- `supabase_client.py` (dead code, replaced by `supabase_ops.py`).
- `supabase_writer.py` (dead code, replaced by `supabase_ops.py`).
- 102 malformed URLs from `institutions.py` seeds (markdown-link-wrapped placeholders).

### Added
- **AI extraction**: NVIDIA NIM integration (Qwen / Llama) for structured extraction (`ai_extractor.py` + `extraction_models.py`).
- **Website mapper** (`website_mapper.py`): sitemap/robots.txt/DDG-based URL discovery with priority scoring across 8 categories.
- **Discovery module** (`discovery.py`): NUC, NBTE, NCCE, NMCN, JAMB connectors for refreshing institution seeds from regulatory sources.
- **Eligibility engine** (`eligibility.py`): O-Level/UTME/Post-UTME/catchment/ELDS scoring with alternative-program finder.
- **Supabase Storage** (`storage.py`): boto3 S3 client for HTML/PDF/Markdown/screenshot uploads to `crawl-assets` and `institution-assets` buckets.
- **Sprint A→G migrations**: 12 split SQL files for Supabase Dashboard application (10_extensions_enums through 99_end_comment).
- **Column migrations**: `migrations/02_add_all_columns.sql` — 200+ `ADD COLUMN IF NOT EXISTS` to fix existing tables.
- **Atomic + cross-platform locking** for `state.json` writes (`resume.py` — temp+rename+fsync + `msvcrt`/`fcntl`).
- **DDG circuit breaker** in `crawl4ai_client._ddg_post` (trips after 3 consecutive 429s, blocks 5 minutes).
- **httpx error retry** in `supabase_ops.run_with_retry` (ConnectError, ReadError, ConnectTimeout, ReadTimeout).
- **Metrics module** (`metrics.py`): thread-safe counters for pages, institutions, AI success, upserts, rate-limits.
- **`DRY_RUN` flag** in `scraper.py` (skips Supabase + storage when True).
- **9 new upserts wired** in `upsert_full_institution`: course_aliases, subjects, olevel_requirements, utme_requirements, direct_entry, post_utme, aggregate_formula, admission_news.
- **CI workflow** (`.github/workflows/ci.yml`): ruff lint, mypy type-check, pytest on every push.
- **Branch mapping rule**: each sprint lives on its own remote branch (`crawl-N`) — Sprint N+1 → `crawl-(N+2)`.

### Fixed
- `fees_parser.py:105` — identical-branch year extraction bug.
- `scraper.py:457-462` — dead block (broken `and`/`or` precedence + `pass` body).
- `ai_extractor.py` — null-guard for empty `content` in API response.
- 44 state casing inconsistencies in `institutions.py` (`kogi` → `Kogi`, `X State` → `X`, cities → parent state).

### Consolidated
- `slugify`: single source in `utils.py` (removed duplicate in `supabase_ops.py`).
- `ELDS_STATES`: single source in `utils.py` (removed duplicates in `eligibility.py`, `parsers/catchment_parser.py`, `migrations/migrate_to_kb.py`, `extraction_models.py` SYSTEM_PROMPT — now uses `format()` template).

## [0.1.0] — Initial release (2026-02)

- Firecrawl-based scraper for Nigerian tertiary institutions.
- Supabase integration with 11-table flat schema.
- 314 institution seeds.
- DuckDuckGo search via raw `httpx` POST.
- 7-table normalized KB writer (SQLite local).
