# Deployment Guide — CKAP Crawler

Free-tier deployment using GitHub Actions + direct GitHub API trigger.

## Architecture

```
campuscompassapp.com admin
        │
        │ POST Authorization: Bearer <GITHUB_PAT>
        ▼
GitHub API: /repos/molaleye38/campus-crawler/dispatches
        │
        │ event_type: run-crawl
        ▼
GitHub Actions: crawl-dispatch.yml
        │
        │ ck-crawl CLI
        ▼
Supabase DB (24 tables) + Storage
```

## One-time Setup

### 1. GitHub PAT for dispatching workflow runs

You need a fine-grained PAT so your admin UI can trigger workflows.

**Walkthrough:**

1. Open https://github.com/settings/tokens?type=beta (Fine-grained personal access tokens)
2. Click **Generate new token**
3. **Token name**: `crawler-dispatch`
4. **Expiration**: 1 year from today
5. **Resource owner**: `molaleye38` (your user)
6. **Repository access**: **Only select repositories** → pick `campus-crawler`
7. **Permissions** → **Repository permissions**:
   - **Actions**: Read and write (needed for `repository_dispatch` event creation)
8. Click **Generate token**
9. **Copy the token** — you won't see it again.

### 2. Configure GitHub repo secrets

Go to https://github.com/molaleye38/campus-crawler/settings/secrets/actions and add:

| Secret | Value (from your .env) |
|---|---|
| `NVIDIA_API_KEY` | `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` |
| `SUPABASE_URL` | `https://fhqylwughhlxumgpsvho.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZocXlsd3VnaGhseHVtZ3BzdmhvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTQyMzA5NCwiZXhwIjoyMDkwOTk5MDk0fQ.l4AKzTjyYB8Aduh4_Y1pVO3U6V0YTIw1IFyCTY1J4x8` |
| `S3_ENDPOINT` | `https://fhqylwughhlxumgpsvho.storage.supabase.co/storage/v1/s3` |
| `S3_REGION` | `eu-west-1` |
| `S3_ACCESS_KEY` | `0403fbc9e1d1409931f9ad79b9b6c9b0` |
| `S3_SECRET_KEY` | `a5f7c5d238f245bcae227e7a4ff3c8ace3c1ddf2a16a47cd8486c5176a25c4d8` |

### 3. Configure campuscompassapp.com

Add to `campuscompassapp.com/.env`:
```
VITE_GITHUB_PAT=<your-github-pat>
```

The PAT is the same one from Step 1 (fine-grained, `actions: read and write`, single repo).

### 4. Deploy admin UI

Copy `admin/CrawlerAdmin.tsx` into your campuscompassapp.com codebase:

```tsx
import { CrawlerTrigger, CrawlRunStatus } from './components/CrawlerAdmin';

export function AdminPage() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-6">
      <CrawlerTrigger />
      <CrawlRunStatus />
    </div>
  );
}
```

No Supabase Edge Function needed. The admin UI calls GitHub API directly.

## Usage

### Manual trigger from admin UI

1. Open `https://campuscompassapp.com/admin/crawler`
2. Set filters (max, types, state)
3. Click **Run Crawler Now**
4. Watch progress via `CrawlRunStatus` or at https://github.com/molaleye38/campus-crawler/actions

### Manual trigger from GitHub UI

Go to https://github.com/molaleye38/campus-crawler/actions/workflows/crawl-dispatch.yml → **Run workflow** → set inputs → **Run workflow**.

### Direct API trigger (bypasses UI)

```bash
curl -X POST https://api.github.com/repos/molaleye38/campus-crawler/dispatches \
  -H "Authorization: Bearer <github-pat>" \
  -H "Accept: application/vnd.github+json" \
  -d '{"event_type": "run-crawl", "client_payload": {"max_institutions": "10"}}'
```

## Schedule

There is **no automatic schedule** by design — you trigger manually once admission season begins.

Suggested cadence:
- **Late February / early March** (JAMB brochure release): initial bulk crawl
- **Weekly during season** (March–August): catch new announcements
- **Late August**: final cleanup pass

## Backups

The `backup.yml` workflow runs **every Sunday 00:00 UTC** automatically and dumps critical Supabase tables to `backups/<date>/<table>.json` on a `backups/` branch.

- 90-day retention (auto-pruned)
- Restore by `git checkout backups` then `git checkout <date> -- <tables>`

To manually trigger a backup:
- GitHub → Actions → Weekly DB Backup → Run workflow

## Cost

| Component | Free tier usage |
|---|---|
| GitHub Actions | ~30 min/crawl × 5-10 crawls/year = ~5 hr/year (within 2,000 min/mo free) |
| Supabase DB | <50 MB used (within 500 MB free) |
| Supabase Storage | <100 MB used (within 1 GB free) |
| GitHub repo storage | ~50 MB backups (within 1 GB free) |
| **Total** | **$0/month** |

## Troubleshooting

### Crawl fails immediately

Check GitHub Actions run logs. Common causes:
- Missing secret → add via repo settings
- Playwright Chromium install fails → check `microsoft/playwright-actions/setup@v1` is in the workflow
- Network errors → retry the workflow

### Supabase upsert fails

Verify the schema is applied (Sprint A). Run `python _verify_sprint_a.py` to confirm 24 tables reachable.

### Admin UI returns 401 / 403

- PAT expired → generate new PAT (same scopes), update `VITE_GITHUB_PAT`
- PAT lacks `actions: write` scope → regenerate with write permission
- PAT repo access doesn't include `campus-crawler` → regenerate with correct repo access

### Crawl succeeds but Supabase empty

Check `supabase_results` in workflow logs. If `upsert_full_institution` failed silently, verify schema matches `supabase_ops.py` expectations.

## Rotating API keys (yearly)

1. Generate new PAT: GitHub → Settings → Tokens → Generate new
2. Update GitHub repo PAT secret? Not needed — the PAT is the credential itself
3. Update campuscompassapp.com `.env`: `VITE_GITHUB_PAT=<new>`
4. Redeploy campuscompassapp.com

## Security notes

- GitHub PAT is **fine-grained**, scoped to **one repo** (`campus-crawler`), with **`actions: read and write`** only
- PAT is exposed in browser bundle (via `VITE_GITHUB_PAT`) — acceptable for admin-only UI
- Supabase credentials never leave GitHub Actions (stored as encrypted secrets)
- `.gitignore` excludes `.env` and `data/`

## License

MIT