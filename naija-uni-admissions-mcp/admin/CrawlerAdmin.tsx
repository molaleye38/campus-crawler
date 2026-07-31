"""
campuscompassapp.com admin button code — paste into your admin UI page.

Requirements:
1. Set VITE_CRAWL_API_KEY in your campuscompassapp.com .env (must match the
   CRAWL_API_KEY secret on the Supabase Edge Function).
2. Install: `npm install swr` for the status poller (optional).

Two components:
  - CrawlerTrigger: button + form to fire the crawl
  - CrawlRunStatus: poll GitHub Actions status (optional, requires GITHUB_PAT)
"""

import { useState } from 'react';
import useSWR from 'swr';

// =============================================================================
// Component 1: CrawlerTrigger
// =============================================================================

const SUPABASE_FN_URL =
  'https://fhqylwughhlxumgpsvho.supabase.co/functions/v1/trigger-crawl';

const CRAWL_API_KEY = import.meta.env.VITE_CRAWL_API_KEY;

const DEFAULT_TYPES = ['university', 'polytechnic', 'college_of_education'];

export function CrawlerTrigger({ onTriggered }: { onTriggered?: () => void }) {
  const [max, setMax] = useState(50);
  const [types, setTypes] = useState<string[]>(DEFAULT_TYPES);
  const [state, setState] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleType = (t: string) =>
    setTypes((prev) =>
      prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]
    );

  async function handleSubmit() {
    setSubmitting(true);
    setError(null);
    try {
      const resp = await fetch(SUPABASE_FN_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': CRAWL_API_KEY,
        },
        body: JSON.stringify({ max, types: types.join(','), state }),
      });
      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}: ${await resp.text()}`);
      }
      onTriggered?.();
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

      {error && <p className="mt-2 text-red-600 text-sm">{error}</p>}
    </div>
  );
}

// =============================================================================
// Component 2: CrawlRunStatus (optional)
// Polls GitHub Actions API for the most recent workflow run.
// Requires VITE_GITHUB_PAT (Fine-grained PAT with `actions: read` scope).
// =============================================================================

const GITHUB_API = 'https://api.github.com';

async function fetchRun(): Promise<any> {
  const pat = import.meta.env.VITE_GITHUB_PAT;
  if (!pat) return null;
  const resp = await fetch(
    `${GITHUB_API}/repos/molaleye38/campus-crawler/actions/runs?event=repository_dispatch&per_page=1`,
    {
      headers: { Authorization: `Bearer ${pat}` },
    }
  );
  if (!resp.ok) return null;
  const data = await resp.json();
  return data.workflow_runs?.[0] ?? null;
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
// import { CrawlerTrigger, CrawlRunStatus } from './CrawlerAdmin';
//
// export function AdminPage() {
//   return (
//     <div className="grid grid-cols-2 gap-4 p-6">
//       <CrawlerTrigger />
//       <CrawlRunStatus />
//     </div>
//   );
// }
