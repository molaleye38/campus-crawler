# Naija Tertiary Admissions MCP

An MCP (Model Context Protocol) server exposing a single tool, `run_admissions_scrape`, that searches the web for **all accredited Nigerian tertiary institutions** — universities, polytechnics, and colleges of education (federal, state, and private) — and collects structured admission data for each:

- **Basic info** — name, short name, type (federal/state/private), state, city, website, year established
- **Admission requirements** — O-level subjects, UTME subjects, general cut-off, per-course cut-offs, Post-UTME format, direct entry requirements
- **Application process** — steps, portal URL, application/acceptance fees, deadlines
- **Programs & faculties** — with degree (B.Sc/ND/HND/NCE/MBBS etc.) and duration
- **Fee tiers** — tuition per session (NGN + USD converted), indigene vs non-indigene rates
- **Catchment areas** — ELDS / geographical (universities only; polytechnics and COEs marked `none`)
- **Confidence tags** — overall field-coverage score + missing fields list per record

Output formats: `data/institutions.json` + `data/institutions.csv` + `data/institutions.db` (SQLite, 6 tables). Outputs are written incrementally so a crash mid-run doesn't lose work.

## Coverage

| Type | Federal | State | Private | Total | Source |
|---|---|---|---|---|---|
| Universities | 46 | 47 | 7 | ~100 | NUC public list + seed |
| Polytechnics | 4 | 5 | 2 | ~11 | NBTE public list |
| Colleges of Education | 21 | 47 | 185 | ~253 | NCCE public list |
| **Total** | | | | **314 (current seeds)** | |

## Why three institution types?

A student who doesn't meet university cut-off (typically UTME >= 180) has fallback paths:

- **Polytechnics** typically accept UTME >= 120-150, leading to ND (National Diploma, 2 yrs) -> HND (Higher National Diploma, 2 yrs)
- **Colleges of Education** typically accept UTME >= 100, leading to NCE (Nigeria Certificate in Education, 3 yrs); many also offer B.Ed via affiliation with a university

Cross-type queries are first-class -- e.g., "show me all polytechnics in Lagos with cutoff <= 150" works directly against the SQLite database.

## Quick start

### 1. Install

```bash
cd naija-uni-admissions-mcp
uv sync
```

### 2. Install Playwright browser (one-time, ~300MB)

```bash
uv run python -m playwright install chromium
```

### 3. Run the pilot (9 institutions -- 3 of each type)

```bash
uv run python -m naija_admissions.server
```

In any MCP-compatible client (opencode, Claude Desktop, etc.) invoke the tool:

```
run_admissions_scrape(max_institutions: 9)
```

Expect ~10 min runtime (each page takes ~12s via Playwright), and these artifacts in `data/`:

- `state.json` (resume state)
- `institutions.json` (full structured records)
- `institutions.csv` (flat view per institution)
- `fees.csv` (one row per fee tier per institution)
- `programs.csv` (one row per program per institution)
- `institutions.db` (6 tables: institutions, programs, fees, catchment_areas, sources, scrape_runs)

### 4. Continue the full run

```
run_admissions_scrape()
```

Each call resumes from `state.json`. **No API key, no monthly quota** -- Crawl4AI runs locally via Playwright/Chromium. Set `MAX_PAGES_PER_RUN=200` in `.env` to cap a single session.

You can scope to specific institution types:

```
run_admissions_scrape(max_institutions: 50, institution_types: ["polytechnic"])
```

## Tool reference

```python
run_admissions_scrape(
    max_institutions: int | None = None,        # None = scrape everything pending
    institution_types: list[str] = ["university", "polytechnic", "college_of_education"],
    resume: bool = True,                          # skip institutions already complete in state.json
    sample_by_type: bool = True,                  # when max_institutions is set, sample evenly across included types
    force_overwrite: bool = False,                # re-scrape even if already complete
) -> ScrapeResult
```

Returns:

```python
{
    "scraped": int,                  # new records successfully scraped this run
    "failed": int,                   # records that errored and will be retried next run
    "skipped": int,                  # records skipped (already complete OR not in institution_types filter)
    "duration_sec": int,
    "paths": {                       # absolute paths to output artifacts
        "json": "...", "csv": "...", "db": "..."
    },
    "remaining_quota": {             # page counter (was Firecrawl credits, now just a counter)
        "used_this_month": int,
        "limit": 1000000,
        "remaining": int,
        "next_window_starts_on": str,  # ISO date start of next calendar month
    },
    "paused": bool,                  # true if run stopped early due to quota gate
}
```

## opencode registration

Add this to your `opencode.json` (or `~/.config/opencode/opencode.json`):

```json
{
  "mcp": {
    "naija-admissions": {
      "type": "local",
      "command": ["uv", "run", "--directory", "<absolute-path>/naija-uni-admissions-mcp", "python", "-m", "naija_admissions.server"],
      "environment": { "NVIDIA_API_KEY": "${NVIDIA_API_KEY}", "SUPABASE_URL": "${SUPABASE_URL}", "SUPABASE_SERVICE_ROLE_KEY": "${SUPABASE_SERVICE_ROLE_KEY}" },
      "enabled": true
    }
  }
}
```

Then any opencode agent can invoke `run_admissions_scrape` as a tool.

## SQLite schema (6 tables)

```sql
institutions        (id, institution_type, name, short_name, type, state, city, website, year_established, admission_requirements_json, application_process_json, confidence_json, last_updated)
programs            (id, institution_id FK, name, faculty, degree, level, duration_years, affiliated_university)
fees                (id, institution_id FK, program_or_faculty, tuition_per_session_ngn, tuition_per_session_usd, currency, indigene_non_indigene_json, source_url, fee_year)
catchment_areas     (id, institution_id FK, name, details, policy)
sources             (id, institution_id FK, url, provider, accessed_on)
scrape_runs         (id, started_at, ended_at, scraped, failed, paused, credits_used, error)
```

Cross-type query example — "polytechnics in Lagos with cutoff ≤ 150":

```sql
SELECT name, website,
       json_extract(admission_requirements_json, '$.utme_cutoff_general') AS cutoff
FROM institutions
WHERE institution_type = 'polytechnic'
  AND state = 'Lagos'
  AND CAST(json_extract(admission_requirements_json, '$.utme_cutoff_general') AS INT) <= 150;
```

## Resume + quota gate

- `state.json` schema tracks per-institution status: `pending | in_progress | completed | failed`
- `MAX_PAGES_PER_RUN` (default 0 = unlimited) caps pages scraped per invocation; long runs can be resumed by re-invoking the tool.
- Interrupt anytime — re-invoking `run_admissions_scrape(resume=true)` continues exactly from where you left off, even across process restarts.

## Supabase

Production knowledge base lives in Supabase (22 production tables + 2 staging tables, see `supabase_schema.sql`). Apply the schema via Supabase Dashboard → SQL Editor:

1. `migrations/02_add_all_columns.sql` — adds missing columns to existing tables (idempotent)
2. `migrations/10_extensions_enums.sql` through `migrations/99_end_comment.sql` — full schema (split into 12 chunks because the Dashboard truncates large statements)

See `CHANGELOG.md` for the full Firecrawl→Crawl4AI migration history.

## Security note

API keys (`NVIDIA_API_KEY`, `SUPABASE_*`) are read from `os.environ` — never committed to code. `.gitignore` excludes `.env` and `data/`.

## License

MIT
