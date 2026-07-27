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
| Universities | ~43 | ~48 | ~79 | ~270 | NUC public list |
| Polytechnics | ~38 | ~45 | ~70+ | ~150 | Wikipedia (NBTE) |
| Colleges of Education | ~27 | ~54 | ~82 | ~163 | Wikipedia (NCCE) |
| **Total** | | | | **~580** | |

## Why three institution types?

A student who doesn't meet university cut-off (typically UTME >= 180) has fallback paths:

- **Polytechnics** typically accept UTME >= 120-150, leading to ND (National Diploma, 2 yrs) -> HND (Higher National Diploma, 2 yrs)
- **Colleges of Education** typically accept UTME >= 100, leading to NCE (Nigeria Certificate in Education, 3 yrs); many also offer B.Ed via affiliation with a university

Cross-type queries are first-class -- e.g., "show me all polytechnics in Lagos with cutoff <= 150" works directly against the SQLite database.

## Quick start

### 1. Install

Use Python 3.11 or 3.12. The project is intentionally pinned below Python 3.13 because the crawler stack depends on browser/Pydantic tooling that should be tested before adopting newer Python releases.

```bash
cd naija-uni-admissions-mcp
uv sync --extra dev
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
    "remaining_quota": {             # page counter
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
      "environment": { "MAX_PAGES_PER_RUN": "${MAX_PAGES_PER_RUN}" },
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
- Page usage is counted in `state.json` and reset automatically on the 1st of each month (or when you delete `credits_used_month` from state)
- The scraper pauses new work when `MAX_PAGES_PER_RUN` would be exceeded for a single invocation
- Interrupt anytime — re-invoking `run_admissions_scrape(resume=true)` continues exactly from where you left off, even across process restarts

## Security note

Secrets are read from `os.environ` — never commit `.env` values. `.gitignore` excludes `.env` and `data/`.

## License

MIT


## Development checks

Sprint 0's local reliability gate is:

```bash
uv sync --extra dev
uv run ruff check src tests
uv run pytest
uv run mypy src
```

CI runs the same checks on Python 3.11 and 3.12. `mypy` is currently a documented Sprint 0 exception: it runs in CI with `continue-on-error` because the existing codebase has broad untyped Supabase/storage/parser surfaces that need a dedicated typing cleanup sprint. `ruff` and `pytest` remain required gates. If a future dependency requires Python 3.13+, update `requires-python`, CI, and this section in the same change.
