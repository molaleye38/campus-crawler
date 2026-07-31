"""Lightweight metrics counters for CKAP pipeline.

Tracks events in-memory; intended to be reported at end of run via safe_log.
No external metrics dependency — keeps the runtime simple.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PipelineMetrics:
    pages_crawled: int = 0
    institutions_scraped: int = 0
    institutions_failed: int = 0
    ai_extractions_success: int = 0
    ai_extractions_failed: int = 0
    supabase_upserts_success: int = 0
    supabase_upserts_failed: int = 0
    ddg_rate_limit_hits: int = 0
    ddg_circuit_breaker_trips: int = 0
    storage_uploads_success: int = 0
    storage_uploads_failed: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "pages_crawled": self.pages_crawled,
            "institutions_scraped": self.institutions_scraped,
            "institutions_failed": self.institutions_failed,
            "ai_extractions_success": self.ai_extractions_success,
            "ai_extractions_failed": self.ai_extractions_failed,
            "supabase_upserts_success": self.supabase_upserts_success,
            "supabase_upserts_failed": self.supabase_upserts_failed,
            "ddg_rate_limit_hits": self.ddg_rate_limit_hits,
            "ddg_circuit_breaker_trips": self.ddg_circuit_breaker_trips,
            "storage_uploads_success": self.storage_uploads_success,
            "storage_uploads_failed": self.storage_uploads_failed,
        }

    def ai_success_rate(self) -> float:
        total = self.ai_extractions_success + self.ai_extractions_failed
        return self.ai_extractions_success / total if total else 0.0

    def upsert_success_rate(self) -> float:
        total = self.supabase_upserts_success + self.supabase_upserts_failed
        return self.supabase_upserts_success / total if total else 0.0


_metrics = PipelineMetrics()
_lock = threading.Lock()


def get_metrics() -> PipelineMetrics:
    """Get the singleton metrics instance."""
    return _metrics


def inc_pages_crawled(n: int = 1) -> None:
    with _lock:
        _metrics.pages_crawled += n


def inc_institution_scraped() -> None:
    with _lock:
        _metrics.institutions_scraped += 1


def inc_institution_failed() -> None:
    with _lock:
        _metrics.institutions_failed += 1


def inc_ai_success() -> None:
    with _lock:
        _metrics.ai_extractions_success += 1


def inc_ai_failed() -> None:
    with _lock:
        _metrics.ai_extractions_failed += 1


def inc_upsert_success(n: int = 1) -> None:
    with _lock:
        _metrics.supabase_upserts_success += n


def inc_upsert_failed(n: int = 1) -> None:
    with _lock:
        _metrics.supabase_upserts_failed += n


def inc_ddg_rate_limit() -> None:
    with _lock:
        _metrics.ddg_rate_limit_hits += 1


def inc_ddg_circuit_trip() -> None:
    with _lock:
        _metrics.ddg_circuit_breaker_trips += 1


def inc_storage_success(n: int = 1) -> None:
    with _lock:
        _metrics.storage_uploads_success += n


def inc_storage_failed(n: int = 1) -> None:
    with _lock:
        _metrics.storage_uploads_failed += n


def reset() -> None:
    global _metrics
    with _lock:
        _metrics = PipelineMetrics()
