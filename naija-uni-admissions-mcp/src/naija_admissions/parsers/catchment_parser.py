"""Catchment area parser — only relevant for federal/state universities."""

from __future__ import annotations

import re

from ..models import CatchmentArea, CatchmentPolicy, InstitutionType

# Educationally Less Developed States (ELDS) — JAMB's recognized list.
# Used as default for federal universities when explicit catchment not found.
ELDS_STATES = [
    "Adamawa", "Bauchi", "Bayelsa", "Benue", "Borno", "Cross River", "Gombe",
    "Jigawa", "Kaduna", "Kano", "Katsina", "Kebbi", "Kogi", "Kwara", "Nasarawa",
    "Niger", "Plateau", "Rivers", "Sokoto", "Taraba", "Yobe", "Zamfara",
]

_CATCHMENT_PATTERNS = [
    r"catchment\s*(?:area|states?)\s*[:\-]?\s*([^.]+)",
    r"educationally\s*less\s*developed\s*states?\s*[:\-]?\s*([^.]+)",
    r"\bELDS\b\s*[:\-]?\s*([^.]+)",
]

_STATE_HINT_PATTERN = re.compile(
    r"\b(Abia|Adamawa|Akwa\s+Ibom|Anambra|Bauchi|Bayelsa|Benue|Borno|Cross\s+River|Delta|Ebonyi|Edo|Ekiti|Enugu|FCT|Gombe|Imo|Jigawa|Kaduna|Kano|Katsina|Kebbi|Kogi|Kwara|Lagos|Nasarawa|Niger|Ogun|Ondo|Osun|Oyo|Plateau|Rivers|Sokoto|Taraba|Yobe|Zamfara)\b",
)


def parse_catchment(text: str, inst_type: InstitutionType, ownership: str, host_state: str | None) -> list[CatchmentArea]:
    if inst_type != InstitutionType.UNIVERSITY:
        return [CatchmentArea(name="none", policy=CatchmentPolicy.NONE, details="Not applicable to this institution type")]

    if ownership == "private":
        return [CatchmentArea(name="none", policy=CatchmentPolicy.NONE, details="Private university — no catchment policy")]

    found = _find_first(_CATCHMENT_PATTERNS, text)
    if found:
        states = re.split(r"[,;/]|\band\b", found, flags=re.IGNORECASE)
        states = [s.strip(" .:;") for s in states if s.strip(" .:;")]
        if states:
            return [
                CatchmentArea(
                    name="Catchment States",
                    policy=CatchmentPolicy.GEOGRAPHICAL,
                    details=", ".join(states),
                )
            ]

    # Heuristic: collect state mentions near "catchment" context
    ctx_window = 500
    pos = text.lower().find("catchment")
    if pos >= 0:
        window = text[max(0, pos - 100) : pos + ctx_window]
        states = sorted({m.group(1) for m in _STATE_HINT_PATTERN.finditer(window)})
        if states:
            return [
                CatchmentArea(
                    name="Geographical Catchment",
                    policy=CatchmentPolicy.GEOGRAPHICAL,
                    details=", ".join(states),
                )
            ]

    # Fallback: federal universities default to ELDS list; state universities default to host state
    if ownership == "federal":
        return [
            CatchmentArea(
                name="ELDS",
                policy=CatchmentPolicy.ELDS,
                details="Educationally Less Developed States (JAMB default): " + ", ".join(ELDS_STATES),
            )
        ]
    if host_state:
        return [
            CatchmentArea(
                name=f"{host_state} State",
                policy=CatchmentPolicy.GEOGRAPHICAL,
                details=f"State university — priority to {host_state} indigenes",
            )
        ]
    return []


def _find_first(patterns: list[str], text: str) -> str | None:
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m:
            return m.group(1).strip()
    return None
