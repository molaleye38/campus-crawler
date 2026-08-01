"""Budget tracking — neutralized for Crawl4AI (local, no quota).

Previously tracked Firecrawl monthly credits. Now just counts pages scraped
for progress reporting. The 'should_pause' gate is now always False unless
the user sets a hard cap via env var MAX_PAGES_PER_RUN.
"""

from __future__ import annotations

import os

from .resume import state_load
from .utils import now_iso, safe_log

# Legacy constant — kept for backward compat with server.py. No longer enforced.
MONTHLY_LIMIT = 1_000_000
SAFETY_THRESHOLD = MONTHLY_LIMIT - 1

# Optional hard cap via env: MAX_PAGES_PER_RUN=200 will pause after 200 pages this run.
MAX_PAGES_PER_RUN = int(os.environ.get("MAX_PAGES_PER_RUN", "0") or "0")


def _current_month() -> str:
    return now_iso()[:7]


def credits_used_this_month(state: dict) -> int:
    """Returns pages scraped this month (kept for backward compat; just a counter)."""
    month = _current_month()
    quota = state.setdefault("quota", {})
    entry = quota.get(month)
    if not entry:
        quota[month] = {"used": 0, "started_on": now_iso()}
        return 0
    return int(entry.get("used", 0))


def add_credits(state: dict, n: int) -> int:
    """Increment pages-scraped counter (was: firecrawl credits)."""
    month = _current_month()
    quota = state.setdefault("quota", {})
    entry = quota.setdefault(month, {"used": 0, "started_on": now_iso()})
    entry["used"] = int(entry.get("used", 0)) + int(n)
    entry["last_updated"] = now_iso()
    return entry["used"]


def remaining_quota(state: dict) -> int:
    """Always large — Crawl4AI has no quota. Returns 1M - pages_this_month."""
    return max(0, MONTHLY_LIMIT - credits_used_this_month(state))


def should_pause(state: dict, run_start_count: int = 0) -> bool:
    """Pause only if MAX_PAGES_PER_RUN env is set and exceeded this run."""
    if MAX_PAGES_PER_RUN <= 0:
        return False
    used_this_run = credits_used_this_month(state) - run_start_count
    if used_this_run >= MAX_PAGES_PER_RUN:
        safe_log("pages_per_run_pause_reached", used_this_run=used_this_run, limit=MAX_PAGES_PER_RUN)
        return True
    return False


def preflight(state_path) -> tuple[bool, str]:
    """Pre-flight check — for Crawl4AI this is essentially a no-op (always OK)."""
    state = state_load(state_path)
    used = credits_used_this_month(state)
    safe_log("preflight_ok_crawl4ai", pages_this_month=used)
    return True, f"Crawl4AI ready. {used} pages scraped this month. Local — no API quota."
