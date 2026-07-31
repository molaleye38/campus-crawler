# Sprint G (crawl-8) — Ops & Deploy

Tasks:
1. Add GitHub Actions CI (`.github/workflows/ci.yml`): lint (ruff), type-check (mypy), test (pytest), schema dry-run
2. Add metrics counters — pages crawled, institutions scraped/failed, AI success rate, Supabase upsert success rate, DDG rate-limit hits
3. Add `--dry-run` flag to scraper.py (no upserts, no DB writes)
4. Update `pyproject.toml` description (Firecrawl → Crawl4AI, ✓ already done in Sprint B)
5. Update README.md (mentions Firecrawl, ✓ may need update)
6. Write CHANGELOG.md documenting Firecrawl→Crawl4AI migration + 22-table schema unification
7. Decide on production deployment target (hosted MCP / cron / etc.)

Reference: full audit in crawl-1 commit 27d319d (SPRINT_MEMORY.md)
