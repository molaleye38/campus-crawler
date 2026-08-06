"""Tests for resume.py state persistence and crash recovery."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from naija_admissions import resume


def test_state_load_creates_default_when_missing(tmp_path: Path):
    state = resume.state_load(tmp_path / "state.json")
    assert state["version"] == 1
    assert state["completed"] == {}
    assert state["failed"] == {}


def test_state_load_recovers_from_corrupt_file(tmp_path: Path):
    p = tmp_path / "state.json"
    p.write_text("not valid json{{{", encoding="utf-8")
    state = resume.state_load(p)
    assert state["version"] == 1
    assert state["completed"] == {}


def test_state_save_atomic(tmp_path: Path):
    p = tmp_path / "state.json"
    state = resume.default_state()
    state["completed"]["Test University"] = {"institution_type": "university", "type": "federal"}
    resume.state_save(p, state)
    assert p.exists()
    assert not (p.parent / (p.name + ".tmp")).exists()


def test_set_and_clear_in_progress(tmp_path: Path):
    state = resume.default_state()
    resume.set_in_progress(state, "Test Univ")
    assert state["in_progress"] == "Test Univ"
    assert "in_progress_at" in state
    resume.clear_in_progress(state)
    assert state["in_progress"] is None
    assert "in_progress_at" not in state


def test_recover_stale_in_progress_clears_after_30_min(tmp_path: Path):
    state = resume.default_state()
    resume.set_in_progress(state, "Stale Univ")
    state["in_progress_at"] = (datetime.now(timezone.utc) - timedelta(minutes=45)).isoformat()
    recovered = resume.recover_stale_in_progress(state, max_age_min=30)
    assert recovered == "Stale Univ"
    assert state["in_progress"] is None
    assert "in_progress_at" not in state


def test_recover_does_not_clear_fresh_in_progress():
    state = resume.default_state()
    resume.set_in_progress(state, "Fresh Univ")
    recovered = resume.recover_stale_in_progress(state, max_age_min=30)
    assert recovered is None
    assert state["in_progress"] == "Fresh Univ"


def test_recover_handles_missing_in_progress_at():
    state = resume.default_state()
    state["in_progress"] = "Orphan Univ"
    state.pop("in_progress_at", None)
    recovered = resume.recover_stale_in_progress(state, max_age_min=30)
    assert recovered == "Orphan Univ"
    assert state["in_progress"] is None


def test_mark_completed_removes_from_failed():
    state = resume.default_state()
    resume.mark_failed(state, "Test", "boom")
    assert "Test" in state["failed"]
    resume.mark_completed(state, "Test", "university", "federal")
    assert "Test" not in state["failed"]
    assert "Test" in state["completed"]


def test_mark_failed_increments_attempts():
    state = resume.default_state()
    resume.mark_failed(state, "Test", "err1")
    resume.mark_failed(state, "Test", "err2")
    resume.mark_failed(state, "Test", "err3")
    assert state["failed"]["Test"]["attempts"] == 3


def test_pending_seeds_excludes_completed():
    state = resume.default_state()
    state["completed"]["Done Univ"] = {"institution_type": "university", "type": "federal"}
    seeds = [
        type("Seed", (), {"name": "Done Univ"})(),
        type("Seed", (), {"name": "New Univ"})(),
    ]
    pending = resume.pending_seeds(state, seeds)
    assert len(pending) == 1
    assert pending[0].name == "New Univ"


def test_pending_seeds_force_overwrite_returns_all():
    state = resume.default_state()
    state["completed"]["Done Univ"] = {"institution_type": "university", "type": "federal"}
    seeds = [
        type("Seed", (), {"name": "Done Univ"})(),
        type("Seed", (), {"name": "New Univ"})(),
    ]
    pending = resume.pending_seeds(state, seeds, force_overwrite=True)
    assert len(pending) == 2
