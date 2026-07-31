# CKAP Branch Mapping Rule (2026-07-31)
- Each sprint lives on its own remote branch: crawl-N where N = sprint index + 2
- Sequence: Sprint A → crawl-2, Sprint B → crawl-3, Sprint C → crawl-4, Sprint D → crawl-5, etc.
- Each branch is remote-only (no local copy). Work in detached HEAD on `campus-crawler/crawl-N`.
- Each branch carries a SPRINT_MEMORY_*.md summarizing the sprint scope + handoff.

# Sprint → Branch Index
| Sprint | Branch   | Topic                  | Status |
|--------|----------|------------------------|--------|
| A      | crawl-2  | Schema + Storage       | DONE   |
| B      | crawl-3  | Code Cleanup           | ACTIVE |
| C      | crawl-4  | AI Enablement          | PENDING|
| D      | crawl-5  | Seed Data Quality      | PENDING|
| E      | crawl-6  | Reliability            | PENDING|
| F      | crawl-7  | Validation             | PENDING|
| G      | crawl-8  | Ops & Deploy           | PENDING|

# Sprint B (crawl-3) — Code Cleanup
Tasks:
- Delete `supabase_client.py` (dead — flat-schema, conflicts with supabase_ops)
- Delete `supabase_writer.py` (dead — flat-schema, conflicts with supabase_ops)
- Delete `tenacity>=8.2` from pyproject.toml (unused)
- Consolidate `slugify` (currently in utils.py, supabase_ops.py, storage.py — keep utils.py)
- Single-source-of-truth ELDS state list (currently in 4 files: eligibility.py, extraction_models.py SYSTEM_PROMPT, parsers/catchment_parser.py, supabase_schema.sql)
- Fix `fees_parser.py:105` identical-branch bug (year extraction)
- Fix `scraper.py:457-462` dead block (broken `and`/`or` precedence + `pass` body)

Reference: full audit in crawl-1 commit 27d319d (SPRINT_MEMORY.md)
