# Sprint C (crawl-4) — AI Enablement

Tasks:
1. Validate NVIDIA API key works end-to-end
2. Flip `AI_EXTRACTION_ENABLED = True` in scraper.py
3. Fix `content: None` null-guard in ai_extractor.py
4. Wire remaining 13 upserts in `upsert_full_institution()`:
   - `upsert_course_alias`
   - `upsert_subject`
   - `upsert_subject_alias`
   - `upsert_olevel_requirements`
   - `upsert_utme_requirements`
   - `upsert_direct_entry`
   - `upsert_post_utme`
   - `upsert_aggregate_formulas`
   - `record_knowledge_version`
   - `upsert_elds` (or upsert to elds table)
   - `upsert_admission_news`
   - `upsert_deadline` (already wired? verify)
   - `upsert_fees` (already wired? verify)
5. Test E2E with AI enabled on a single institution

Reference: full audit in crawl-1 commit 27d319d (SPRINT_MEMORY.md)
