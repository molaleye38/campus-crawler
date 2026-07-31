# Sprint F (crawl-7) — Validation

Tasks:
1. Run `pytest` — verify all ~80 unit tests pass after Sprint B/C/D/E changes
2. Run `test_full_pipeline.py --no-upsert` — verify Crawl4AI + DDG search + regex parsers work without Supabase
3. Run `test_full_pipeline.py` (with Supabase enabled) — verify full upsert flow
4. Run `test_supabase.py` — verify all upsert functions work against current Supabase schema
5. Run `migrate_kb_to_unified` if legacy KB has data (legacy KB in data/institutions.db)
6. Capture any test failures and fix them before sprint-end

Reference: full audit in crawl-1 commit 27d319d (SPRINT_MEMORY.md)
