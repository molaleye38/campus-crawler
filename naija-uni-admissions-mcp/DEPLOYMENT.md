# Deployment Guide — CKAP Crawler

Free-tier deployment using GitHub Actions + Supabase Edge Functions.

## Architecture

```
campuscompassapp.com admin
        │
        │ POST x-api-key: <CRAWL_API_KEY>
        ▼
Supabase Edge Function: trigger-crawl
        │
        │ POST /repos/.../dispatches
        ▼
GitHub Actions: crawl-dispatch.yml
        │
        │ ck-crawl CLI
        ▼
Supabase DB (24 tables) + Storage
```

## One-time Setup

### 1. GitHub PAT for dispatching workflow runs

You need a fine-grained PAT so the Edge Function can trigger workflows.

**Walkthrough:**

1. Open https://github.com/settings/tokens?type=beta (Fine-grained personal access tokens)
2. Click **Generate new token**
3. **Token name**: `crawler-dispatch`
4. **Expiration**: 1 year (matches your yearly rotation plan)
5. **Resource owner**: `molaleye38` (your user)
6. **Repository access**: **Only select repositories** → pick `campus-crawler`
7. **Permissions** → **Repository permissions**:
   - **Actions**: Read and write (needed for `repository_dispatch` event creation)
8. Click **Generate token**
9. **Copy the token** (you won't see it again) — store it somewhere safe temporarily

### 2. Generate the API key for your admin UI

Pick any random string ≥ 32 chars. Example:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

You'll use this twice:
- As `CRAWL_API_KEY` secret in Supabase Edge Function
- As `VITE_CRAWL_API_KEY` env var in `campuscompassapp.com`

**Rotate yearly** — generate a new one before each admission season.

### 3. Configure GitHub repo secrets

Go to https://github.com/molaleye38/campus-crawler/settings/secrets/actions and add:

| Secret | Value |
|---|---|
| `NVIDIA_API_KEY` | Your NVIDIA NIM API key |
| `SUPABASE_URL` | `https://fhqylwughhlxumgpsvho.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | (from `.env`) |
| `S3_ENDPOINT` | `https://fhqylwughhlxumgpsvho.storage.supabase.co/storage/v1/s3` |
| `S3_REGION` | `eu-west-1` |
| `S3_ACCESS_KEY` | (from `.env`) |
| `S3_SECRET_KEY` | (from `.env`) |

Optional `LOG_LEVEL=INFO` as a **variable** (Settings → Variables).

### 4. Deploy Supabase Edge Function

```bash
# Install Supabase CLI if not already
brew install supabase/tap/supabase   # macOS
# or: scoop install supabase         # Windows

cd naija-uni-admissions-mcp
supabase login
supabase link --project-ref fhqylwughhlxumgpsvho

# Set secrets
supabase secrets set CRAWL_API_KEY=<your-api-key>
supabase secrets set GITHUB_PAT=<your-github-pat>
supabase secrets set GITHUB_REPO=molaleye38/campus-crawler

# Deploy
supabase functions deploy trigger-crawl --no-verify-jwt
```

Verify:
```bash
curl -X POST https://fhqylwughhlxumgpsvho.supabase.co/functions/v1/trigger-crawl \
  -H "Content-Type: application/json" \
  -H "x-api-key: <your-api-key>" \
  -d '{"max": 5}'
```

Should return `{"triggered": true, ...}` and start a workflow run.

### 5. Wire admin button into `campuscompassapp.com`

Copy `admin/CrawlerAdmin.tsx` into your app:

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

Add to `campuscompassapp.com/.env`:
```
VITE_CRAWL_API_KEY=<your-api-key>
VITE_GITHUB_PAT=<optional-pat-for-status-polling>
```

The status poller (`CrawlRunStatus`) is optional. It needs a separate PAT (with `actions: read` scope, not write). If you don't want to expose that, just use `CrawlerTrigger` alone and watch the run on GitHub directly.

## Usage

### Manual trigger from admin UI

1. Open `https://campuscompassapp.com/admin/crawler`
2. Set filters (max, types, state)
3. Click **Run Crawler Now**
4. (Optional) Watch progress via `CrawlRunStatus` or at https://github.com/molaleye38/campus-crawler/actions

### Manual trigger from GitHub UI

Go to https://github.com/molaleye38/campus-crawler/actions/workflows/crawl.yml → **Run workflow** → set inputs → **Run workflow**.

### Direct API trigger (bypasses Supabase)

For testing, you can dispatch the workflow directly:

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
| Supabase Edge Functions | 5-10 invocations/month (within 500K free) |
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

### API key mismatch

The Edge Function returns 401 if `x-api-key` doesn't match. Update both `CRAWL_API_KEY` (Supabase secret) and `VITE_CRAWL_API_KEY` (campuscompassapp.com env) at the same time.

### PAT expired

GitHub will return 401 from the Edge Function. Generate a new PAT, update `GITHUB_PAT` secret in Supabase.

## Rotating API keys (yearly)

1. Generate new API key: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
2. Update Supabase secret: `supabase secrets set CRAWL_API_KEY=<new>`
3. Update `campuscompassapp.com/.env`: `VITE_CRAWL_API_KEY=<new>`
4. Redeploy edge function: `supabase functions deploy trigger-crawl --no-verify-jwt`
5. Redeploy `campuscompassapp.com`

## Rotating GitHub PAT (yearly)

1. Generate new PAT (same scopes as before)
2. Update Supabase secret: `supabase secrets set GITHUB_PAT=<new>`
3. (No other changes needed — workflows don't reference the PAT)
