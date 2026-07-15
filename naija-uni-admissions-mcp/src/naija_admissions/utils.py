"""Shared utilities: logging, currency conversion, polite delays."""

from __future__ import annotations

import asyncio
import os
import random
from datetime import UTC
from typing import Any

import structlog

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(getattr(__import__("logging"), LOG_LEVEL, 0)),
    cache_logger_on_first_use=True,
)

log = structlog.get_logger("naija_admissions")


def get_ngn_per_usd() -> float:
    try:
        return float(os.environ.get("NGN_PER_USD", "1600"))
    except ValueError:
        return 1600.0


def ngn_to_usd(ngn: int | None) -> int | None:
    if ngn is None:
        return None
    return round(ngn / get_ngn_per_usd())


async def polite_delay(min_s: float = 1.5, max_s: float = 3.0) -> None:
    await asyncio.sleep(random.uniform(min_s, max_s))


def now_iso() -> str:
    from datetime import datetime
    return datetime.now(UTC).isoformat()


def today_iso() -> str:
    from datetime import datetime
    return datetime.now(UTC).date().isoformat()


def slugify(name: str) -> str:
    slug = name.lower().strip()
    for ch in " ,.-'/":
        slug = slug.replace(ch, "_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_")


def http_safe_url(u: str | None) -> str | None:
    if not u:
        return None
    u = u.strip()
    if not u:
        return None
    if u.startswith("http://") or u.startswith("https://"):
        return u
    return f"https://{u}"


def trunc(s: str, n: int = 200) -> str:
    return s if len(s) <= n else s[: n - 1] + "\u2026"


def safe_log(event: str, **kw: Any) -> None:
    try:
        log.info(event, **kw)
    except Exception:
        pass
