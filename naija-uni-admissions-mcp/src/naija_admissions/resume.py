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
import os
import sys
import tempfile
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


def _acquire_lock(p: Path) -> int | None:
    """Acquire exclusive file lock (cross-platform). Returns fd or None."""
    lock_path = p.with_suffix(p.suffix + ".lock")
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o666)
        if sys.platform == "win32":
            import msvcrt
            try:
                msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
            except OSError:
                os.close(fd)
                return None
        else:
            import fcntl
            try:
                fcntl.flock(fd, fcntl.LOCK_EX)
            except OSError:
                os.close(fd)
                return None
        return fd
    except OSError:
        return None


def _release_lock(fd: int | None) -> None:
    """Release the lock acquired by _acquire_lock."""
    if fd is None:
        return
    try:
        if sys.platform == "win32":
            import msvcrt
            try:
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
        else:
            import fcntl
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except OSError:
                pass
    finally:
        os.close(fd)


def state_save(path: str | Path, state: dict[str, Any]) -> None:
    """Atomic save: write to temp file, then rename. Acquires cross-platform lock."""
    state["updated_at"] = now_iso()
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd = _acquire_lock(p)
    try:
        content = json.dumps(state, indent=2)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(p.parent),
            prefix=".state_",
            suffix=".tmp",
            delete=False,
        ) as f:
            tmp = Path(f.name)
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        tmp.replace(p)
    finally:
        _release_lock(fd)


def state_load(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return default_state()
    fd = _acquire_lock(p)
    try:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return default_state()
        for k in ("completed", "failed", "quota", "scrape_runs"):
            data.setdefault(k, {} if k != "scrape_runs" else [])
        return data
    finally:
        _release_lock(fd)


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
