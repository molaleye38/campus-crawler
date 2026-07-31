# Sprint D (crawl-5) — Seed Data Quality

Tasks:
1. Audit institutions.py seed file for malformed URLs and bad state casing
2. Fix broken URLs like `https://[none.edu.ng](https://none.edu.ng)` → remove or repair
3. Normalize state casing (`kogi` → `Kogi`, `Jigwa` → `Jigawa`, `Yola` → `Adamawa` state, etc.)
4. Re-run discovery.py to refresh seeds (current 314 vs target ~580)
5. Implement NBTEConnector (currently a stub returning empty list)
6. Implement JAMBConnector (currently a stub — needs IBASS auth flow OR replace with public JAMB brochure scraping)

Reference: full audit in crawl-1 commit 27d319d (SPRINT_MEMORY.md)
