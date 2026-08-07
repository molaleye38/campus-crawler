"""State persistence + resume logic.

state.json schema:
{
    "version": 1,
    "created_at": "<iso>",
    "updated_at": "<iso>",
    "completed": {"<name>": {"institution_type": "...", "type": "...", "completed_at": "<iso>"}},
    "failed": {"<name>": {"error": "...", "attempts": N, "last_failed_at": "<iso>"}},
    "in_progress": "<name> | null",
    "quota": {
        "<YYYY-MM>": {"used": N, "started_on": "<iso>", "last_updated": "<iso>"}
    },
    "scrape_runs": [{"id": 0, "started_at": "...", "ended_at": "...", "scraped": N, "failed": N, "paused": bool, "credits_used": N}]
}
"""

from __future__ import annotations

import json
from datetime import UTC
from pathlib import Path
from typing import Any

from .utils import now_iso


def default_state() -> dict[str, Any]:
    return {
        "version": 1,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "completed": {},
        "failed": {},
        "in_progress": None,
        "quota": {},
        "scrape_runs": [],
    }


def state_load(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return default_state()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        for k in ("completed", "failed", "quota", "scrape_runs"):
            data.setdefault(k, {} if k != "scrape_runs" else [])
        return data
    except Exception:
        return default_state()


def state_save(path: str | Path, state: dict[str, Any]) -> None:
    state["updated_at"] = now_iso()
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    tmp.replace(p)


def mark_completed(state: dict[str, Any], name: str, institution_type: str, type_: str) -> None:
    state.setdefault("completed", {})[name] = {
        "institution_type": institution_type,
        "type": type_,
        "completed_at": now_iso(),
    }
    state.get("failed", {}).pop(name, None)
    if state.get("in_progress") == name:
        state["in_progress"] = None


def mark_failed(state: dict[str, Any], name: str, error: str, max_attempts: int = 3) -> None:
    f = state.setdefault("failed", {})
    entry = f.get(name, {"attempts": 0, "error": None, "last_failed_at": None})
    entry["attempts"] = int(entry.get("attempts", 0)) + 1
    entry["error"] = error[:500]
    entry["last_failed_at"] = now_iso()
    f[name] = entry
    if state.get("in_progress") == name:
        state["in_progress"] = None


def set_in_progress(state: dict[str, Any], name: str) -> None:
    state["in_progress"] = name
    state["in_progress_at"] = now_iso()


def clear_in_progress(state: dict[str, Any]) -> None:
    state["in_progress"] = None
    state.pop("in_progress_at", None)


def recover_stale_in_progress(state: dict[str, Any], max_age_min: int = 30) -> str | None:
    """If in_progress is older than max_age_min minutes (default 30), clear it.

    Returns the recovered institution name (or None if nothing was stale).
    Useful on startup to detect killed/interrupted runs.
    """
    in_progress = state.get("in_progress")
    if not in_progress:
        return None
    in_progress_at = state.get("in_progress_at")
    if not in_progress_at:
        clear_in_progress(state)
        return in_progress
    from datetime import datetime, timedelta
    try:
        ts = datetime.fromisoformat(in_progress_at.replace("Z", "+00:00"))
    except Exception:
        clear_in_progress(state)
        return in_progress
    age = datetime.now(UTC) - ts
    if age > timedelta(minutes=max_age_min):
        clear_in_progress(state)
        return in_progress
    return None


def start_scrape_run(state: dict[str, Any]) -> int:
    runs = state.setdefault("scrape_runs", [])
    run_id = len(runs)
    runs.append(
        {
            "id": run_id,
            "started_at": now_iso(),
            "ended_at": None,
            "scraped": 0,
            "failed": 0,
            "paused": False,
            "credits_used": 0,
        }
    )
    return run_id


def end_scrape_run(
    state: dict[str, Any],
    run_id: int,
    scraped: int,
    failed: int,
    paused: bool,
    credits_used: int,
) -> None:
    runs = state.get("scrape_runs", [])
    if 0 <= run_id < len(runs):
        runs[run_id].update(
            {
                "ended_at": now_iso(),
                "scraped": scraped,
                "failed": failed,
                "paused": paused,
                "credits_used": credits_used,
            }
        )


def is_completed(state: dict[str, Any], name: str) -> bool:
    return name in state.get("completed", {})


def pending_seeds(
    state: dict[str, Any],
    seeds: list,
    force_overwrite: bool = False,
) -> list:
    if force_overwrite:
        return list(seeds)
    completed = state.get("completed", {})
    return [s for s in seeds if s.name not in completed]
