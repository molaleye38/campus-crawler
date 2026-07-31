"""Parser for fees — tuition, application, acceptance."""

from __future__ import annotations

import re

from ..models import FeeTier
from ..utils import ngn_to_usd

_TUITION_PATTERNS = [
    r"tuition\s*(?:fee)?\s*[:\-]?\s*(?:naira|n\u20a6|\u20a6|ngn)?\s*(\d[\d,]{3,})",
    r"school\s*fees?\s*[:\-]?\s*(?:naira|n\u20a6|\u20a6|ngn)?\s*(\d[\d,]{3,})",
    r"(?:naira|n\u20a6|\u20a6|ngn)\s*(\d[\d,]{3,})",
    r"fee[:\s]*\u20a6?\s*(\d[\d,]{3,})",
]

_APPLICATION_PATTERNS = [
    r"application\s*(?:form\s*)?fee\s*[:\-]?\s*(?:naira|n\u20a6|\u20a6|ngn)\s*(\d[\d,]+)",
    r"form\s*fee\s*[:\-]?\s*(?:naira|n\u20a6|\u20a6|ngn)\s*(\d[\d,]+)",
]

_ACCEPTANCE_PATTERNS = [
    r"acceptance\s*fee\s*[:\-]?\s*(?:naira|n\u20a6|\u20a6|ngn)\s*(\d[\d,]+)",
]

_PORTAL_PATTERNS = [
    r"(?:portal|application\s+portal|admissions?\s+portal)\s*[:\-]?\s*(https?://\S+)",
    r"\bportal[:\s]+(https?://\S+)",
]

_DEADLINE_PATTERNS = [
    r"(?:deadline|closing\s+date)\s*[:\-]?\s*([^\n.]+)",
]

_STEPS_PATTERNS = [
    r"how\s+to\s+apply\s*[:\-]?\s*([^.]+(?:\.[^.]+){0,5})",
    r"application\s+steps?\s*[:\-]?\s*([^.]+(?:\.[^.]+){0,5})",
]

_INDIGENE_PATTERN = re.compile(
    r"indigene[^\n]*?(\d[\d,]+)\s*[\n\r].{0,80}?non[-\s]?indigene[^\n]*?(\d[\d,]+)",
    re.IGNORECASE | re.DOTALL,
)

_FEE_YEAR_PATTERN = re.compile(r"\b(20\d{2})/(?:20)?(\d{2})\s*(?:academic\s*(?:year|session)|session)\b")


def _parse_ngn(s: str | None) -> int | None:
    if not s:
        return None
    digits = re.sub(r"[^\d]", "", s)
    if not digits:
        return None
    try:
        return int(digits)
    except ValueError:
        return None


def _find_first(patterns: list[str], text: str) -> str | None:
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m:
            return m.group(1).strip()
    return None


def parse_fees(text: str, source_url: str) -> list[FeeTier]:
    tiers: list[FeeTier] = []

    # Group context lines and find all NGN amounts with surrounding faculty hints
    for line in text.split("\n"):
        line = line.strip()
        if not line or len(line) < 4:
            continue
        for pat in _TUITION_PATTERNS:
            m = re.search(pat, line, re.IGNORECASE)
            if m:
                ngn = _parse_ngn(m.group(1))
                if not ngn or ngn < 1000:
                    continue
                ctx_low = line.lower()
                program_label = "general"
                if "engineering" in ctx_low:
                    program_label = "Engineering"
                elif "medicine" in ctx_low or "medical" in ctx_low or "mbbs" in ctx_low:
                    program_label = "Medicine"
                elif "law" in ctx_low:
                    program_label = "Law"
                elif "science" in ctx_low:
                    program_label = "Sciences"
                elif "arts" in ctx_low or "humanities" in ctx_low:
                    program_label = "Arts"
                indigene_pair: dict[str, int] | None = None
                im = _INDIGENE_PATTERN.search(line)
                if im:
                    ind = _parse_ngn(im.group(1))
                    nond = _parse_ngn(im.group(2))
                    if ind and nond:
                        indigene_pair = {"indigene": ind, "non_indigene": nond}
                fy = None
                fm = _FEE_YEAR_PATTERN.search(text)
                if fm:
                    try:
                        fy = int(fm.group(1)) if fm.group(1) else (2000 + int(fm.group(2)) if fm.group(2) else None)
                        if fy is not None and (fy < 2000 or fy > 2100):
                            fy = None
                    except ValueError:
                        fy = None
                tiers.append(
                    FeeTier(
                        program_or_faculty=program_label,
                        tuition_per_session_ngn=ngn,
                        tuition_per_session_usd=ngn_to_usd(ngn),
                        currency="NGN",
                        indigene_vs_non_indigene=indigene_pair,
                        source_url=source_url,
                        fee_year=fy,
                    )
                )
                break

    # Dedupe by program label
    seen: set[str] = set()
    unique: list[FeeTier] = []
    for t in tiers:
        if t.program_or_faculty in seen:
            continue
        seen.add(t.program_or_faculty)
        unique.append(t)
    return unique


def parse_application_process(text: str) -> dict | None:
    portal = _find_first(_PORTAL_PATTERNS, text)
    deadline = _find_first(_DEADLINE_PATTERNS, text)
    appl = _parse_ngn(_find_first(_APPLICATION_PATTERNS, text))
    accept = _parse_ngn(_find_first(_ACCEPTANCE_PATTERNS, text))
    steps_raw = _find_first(_STEPS_PATTERNS, text)
    steps: list[str] = []
    if steps_raw:
        steps = [s.strip(" -*0123456789.\t") for s in re.split(r"\n|\.(?=\s)", steps_raw) if s.strip()][:10]

    if not any([portal, deadline, appl, accept, steps]):
        return None
    return {
        "steps": steps,
        "portal_url": portal,
        "application_fee_ngn": appl,
        "acceptance_fee_ngn": accept,
        "deadlines": deadline,
    }
