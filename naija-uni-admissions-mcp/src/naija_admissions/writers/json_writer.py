"""Incremental JSON writer — writes the full institutions list after each record."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..models import Institution


def write_json(path: str | Path, institutions: list[Institution]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data: list[dict[str, Any]] = [
        inst.model_dump(mode="json", exclude_none=False) for inst in institutions
    ]
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)
