/**
 * campuscompassapp.com admin components — paste into your admin UI page.
 *
 * Requirements:
 * 1. Set VITE_GITHUB_PAT in your campuscompassapp.com .env (fine-grained PAT with `actions: write` scope)
 *    - This PAT must have access to molaleye38/campus-crawler repo
 * 2. Install: `npm install swr` for the status poller (optional)
 *
 * Two components:
 *   - CrawlerTrigger: button + form to fire the crawl via GitHub API
 *   - CrawlRunStatus: poll GitHub Actions status (optional)
 */

import { useState } from 'react';
import useSWR from 'swr';

const GITHUB_API = 'https://api.github.com';
const REPO = 'molaleye38/campus-crawler';

const DEFAULT_TYPES = ['university', 'polytechnic', 'college_of_education'];

export function CrawlerTrigger({ onTriggered }: { onTriggered?: () => void }) {
  const [max, setMax] = useState(50);
  const [types, setTypes] = useState<string[]>(DEFAULT_TYPES);
  const [state, setState] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const toggleType = (t: string) =>
    setTypes((prev) =>
      prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]
    );

  async function handleSubmit() {
    if (!types.length) {
      setError('Select at least one institution type');
      return;
    }
    setSubmitting(true);
    setError(null);
    setSuccess(false);

    try {
      const pat = import.meta.env.VITE_GITHUB_PAT;
      if (!pat) {
        throw new Error('Missing VITE_GITHUB_PAT in .env');
      }

      const resp = await fetch(
        `${GITHUB_API}/repos/${REPO}/dispatches`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${pat}`,
            Accept: 'application/vnd.github+json',
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            event_type: 'run-crawl',
            client_payload: {
              max_institutions: String(max),
              institution_types: types.join(','),
              state: state.trim() || '',
            },
          }),
        }
      );

      if (!resp.ok) {
        const txt = await resp.text();
        throw new Error(`HTTP ${resp.status}: ${txt}`);
      }

      setSuccess(true);
      onTriggered?.();

      // Auto-clear success after 3s
      setTimeout(() => setSuccess(false), 3000);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="p-4 border rounded">
      <h2 className="text-lg font-semibold mb-4">Run Crawler</h2>

      <label className="block mb-2">
        <span className="text-sm">Max institutions</span>
        <input
          type="number"
          value={max}
          onChange={(e) => setMax(Number(e.target.value))}
          className="block w-full mt-1 border rounded px-2 py-1"
          min={1}
          max={500}
        />
      </label>

      <fieldset className="mb-2">
        <legend className="text-sm">Institution types</legend>
        {DEFAULT_TYPES.map((t) => (
          <label key={t} className="inline-flex items-center mr-3">
            <input
              type="checkbox"
              checked={types.includes(t)}
              onChange={() => toggleType(t)}
            />
            <span className="ml-1">{t}</span>
          </label>
        ))}
      </fieldset>

      <label className="block mb-4">
        <span className="text-sm">State filter (optional)</span>
        <input
          type="text"
          value={state}
          onChange={(e) => setState(e.target.value)}
          className="block w-full mt-1 border rounded px-2 py-1"
          placeholder="e.g. Lagos"
        />
      </label>

      <button
        onClick={handleSubmit}
        disabled={submitting || types.length === 0}
        className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50"
      >
        {submitting ? 'Triggering…' : 'Run Crawler Now'}
      </button>

      {success && (
        <p className="mt-2 text-green-600 text-sm">
          Crawl triggered! Check <a href={`https://github.com/${REPO}/actions`} target="_blank" rel="noreferrer" className="underline">GitHub Actions</a> for progress.
        </p>
      )}

      {error && <p className="mt-2 text-red-600 text-sm">{error}</p>}
    </div>
  );
}

// =============================================================================
// Component 2: CrawlRunStatus (optional)
// Polls GitHub Actions API for the most recent workflow run.
// Requires VITE_GITHUB_PAT (same PAT, needs `actions: read` scope).
// =============================================================================

async function fetchRun(): Promise<any> {
  const pat = import.meta.env.VITE_GITHUB_PAT;
  if (!pat) return null;

  try {
    const resp = await fetch(
      `${GITHUB_API}/repos/${REPO}/actions/runs?event=repository_dispatch&per_page=1`,
      {
        headers: { Authorization: `Bearer ${pat}` },
      }
    );
    if (!resp.ok) return null;
    const data = await resp.json();
    return data.workflow_runs?.[0] ?? null;
  } catch {
    return null;
  }
}

export function CrawlRunStatus() {
  const { data: run, error } = useSWR('crawl-run', fetchRun, {
    refreshInterval: 10000,
  });

  if (error) return <p className="text-red-600 text-sm">Status unavailable</p>;
  if (!run) return <p className="text-gray-600 text-sm">No runs yet</p>;

  const statusColor: Record<string, string> = {
    success: 'text-green-600',
    failure: 'text-red-600',
    in_progress: 'text-blue-600',
    queued: 'text-yellow-600',
  };

  return (
    <div className="p-4 border rounded">
      <h3 className="font-semibold">Latest Crawl Run</h3>
      <p>
        <span className={statusColor[run.conclusion ?? run.status] ?? 'text-gray-600'}>
          {run.conclusion ?? run.status}
        </span>
        {' · '}
        <a href={run.html_url} target="_blank" rel="noreferrer" className="underline">
          View on GitHub →
        </a>
      </p>
      <p className="text-xs text-gray-500">
        Started: {new Date(run.created_at).toLocaleString()}
      </p>
    </div>
  );
}

// =============================================================================
// Example page usage:
// =============================================================================
//
// import { CrawlerTrigger, CrawlRunStatus } from './components/CrawlerAdmin';
//
// export function AdminPage() {
//   return (
//     <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-6">
//       <CrawlerTrigger />
//       <CrawlRunStatus />
//     </div>
//   );
// }