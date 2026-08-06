# Sprint 9: Scrapy Integration — Design Proposal

**Branch:** `crawl-17`
**Status:** Proposal / Architecture
**Goal:** Introduce Scrapy as a fast, headless discovery + initial-extract layer alongside Crawl4AI

---

## Problem Statement

The current pipeline is 100% Crawl4AI-based:
1. DuckDuckGo search for admission-related pages
2. Crawl4AI renders each page in Playwright Chromium
3. regex parsers + optional AI extraction
4. Supabase upsert

**Problems:**
- **Slow:** Each page requires 5-20s for browser render + network. 20 inst x 4 URLs = up to 27 min.
- **Expensive:** Browser-based scraping burns CPU in CI. Each GH Actions run has a 180min cap.
- **No structural scraping:** We regex-parse flat markdown. Nigerian portals like JAMB's Central Admissions Processing System (CAPS) and NUC's accreditation directory have structured data (tables, lists, forms) that regex struggles with.
- **Discovery blind spots:** Only has 270+150+163 = ~583 seeds. New institutions, renamed institutions, satellite campuses are not captured.

**Goal: Scrapy spider = 10-20x faster than Crawl4AI for sites that don't need JavaScript.**

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Scrapy Layer (new)                           │
│                                                                      │
│  ┌───────────────────┐  ┌────────────────────┐  ┌────────────────┐  │
│  │ JambBrochureSpider │  │ NuAccreditationSpider│  │ PortalSpider  │  │
│  │ (jamb.gov.ng)      │  │ (nuc.edu.ng)         │  │ (uni.edu.ng)  │  │
│  └─────────┬─────────┘  └──────────┬─────────┘  └───────┬────────┘  │
│            │ crawl IOSG brochure   │ crawl accredited   │ crawl     │
│            │ (UTME reqs, cutoffs,  │ programs list      │ admissions│
│            │ fees)                 │                    │ portal    │
│            ▼                       ▼                    ▼           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              scrapy.doc.find(): export                         │   │
│  │  → discovered_institutions.json (enriched from real data)     │   │
│  │  → jamb_brochure.jsonlines (UTME+O'Level+cutoffs per course) │   │
│  │  → portal_programs.jsonlines (faculties+programs from portals)│   │
│  └─────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     Crawl4AI Layer (existing)                        │
│                                                                      │
│  Scrapy-enriched seeds → DuckDuckGo search → Playwright render →    │
│  regex + AI extraction → validation → Supabase upsert               │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Sprint Scope & Tasks

### 1. Add Scrapy as dev dependency (`crawl-17-spiders`)
- `uv add scrapy`
- Create `spiders/` directory under `src/naija_admissions/`
- Create `scrapy.cfg`

### 2. JAMB Brochure Spider
**Target:** `https://jamb.gov.ng/ibass` (JAMB IBASS E-brochure) — central authority for UTME requirements.
**Approach:** Mitmproxy crawler or manual CSV export. Many JAMB pages are rendered with server-side PHP. Pure httpx request + BeautifulSoup/parsel ∩ Scrapy response class.
**Output:** `jamb_programmes.jsonlines` — one JSON line per course-programme pair with UTME subjects, O-Level subjects, cutoffs.

### 3. NUC Accreditation Spider
**Target:** `https://www.nuc.edu.ng/nigerian-universities` — NUC directory of accredited universities and programmes.
**Output:** `nuc_accredited_programs.jsonlines` — institution name, faculty, degree, accreditation status, expiry.

### 4. Portal Spider (per-school admission pages)
Use `LinkExtractor` + the URL seed list from `institutions.py` to crawl each school's admissions portal:
- CSS selector for application portal links, payment portals, requirements pages
- Extract tables (tuition fees), `<ol>` lists (admission steps), `<ul>` lists (requirements)
- Works for 60-70% of schools with static admission pages

### 5. Feed Exporter Integration
Wire Scrapy output into the existing pipeline:
```yaml
# settings.py / spider custom_settings
FEEDS:
    data/jamb_programmes.jsonlines: { "filter": "jamb" }
    data/nuc_accreditation.jsonlines: { "filter": "nuc" }
    data/portal_programmes.jsonlines: { "filter": "portal" }
```

### 6. CLI Integration
Add `--scrapy-discover` flag to `ck-crawl`:
```bash
uv run ck-crawl --scrapy-discover  # runs discovery spiders first, then Crawl4AI
uv run ck-crawl --scrapy-only      # runs Scrapy but not Crawl4AI
```

### 7. Fallback: Scrapy spiders can reuse Crawl4AI
For JavaScript SPAs, `scrapy-playwright` can call Playwright. This lets us set HTTP concurrency to 16 (vs Crawl4AI's max 2) for 80% of sites, while reserving browser rendering for the stubborn 20%.

---

## Success Metrics

| Metric | Before (Crawl4Ai only) | After (Scrapy + Crawl4AI) |
|--------|----------------------|----------------------------|
| Per-institution time | 45-180s | 10-15s (90% sites) |
| 20 institutions | ~60 min | ~10-15 min |
| Per-run cost | 1 GitHub runner x 2h | 1 GitHub runner x 30min |
| Known programmes | parser-only guesses | 4x+ richer from JAMB/NUC |
| O-Level subj per prog | none | 5 subjects per programme |
| Redetect new institutions | manual seed update | auto-discovered from NUC portal |

---

## Risks & Mitigations

1. **JAMB bans IP of scraper:** Mitigate with PolitePolicy (10+ second delay between requests), rotate User-Agent.
2. **NUC portal changes layout:** Mitigate with XPath fallback + health check after every weekly scrape.
3. **Scrapy + asyncio confusion:** Scrapy runs in Twisted event loop. Keep it isolated: Run as a subprocess (CLI invokes `scrapy crawl` from `uv run scrapy crawl all`). Do NOT integrate into the async MCP server.
4. **Playwright-scrapy dep conflicts:** Avoid `scrapy-playwright` initially. Use plain Scrapy for the 80% of static sites. Leave JavaScript sites to Crawl4Ai.

---

## Implementation Order (Spint 9 tasks)

1. Install scrapy, create project scaffold
2. Build JambBrochureSpider (highest-value data source)
3. Build NucationalSpider  
4. Build PortalSpider (LinkExtractor)
5. Wire FEEDS config
6. Add `--scrapy-discover` / `--scrapy-only` to CLI
7. Add tests (SpiderContract)
8. Documentation for data calibration

**Estimated time:** 3 hours
**Branch:** `crawl-17` → squash to `Crawl4AI+scrapy` workflow