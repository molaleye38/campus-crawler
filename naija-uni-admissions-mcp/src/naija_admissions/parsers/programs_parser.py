"""Programs/faculties parser — recognizes ND/HND/NCE/B.Sc/B.A/B.Eng/MBBS/LL.B."""

from __future__ import annotations

import re

from ..models import InstitutionType, Program

_FACULTIES_PATTERN = re.compile(
    r"facult(?:y|ies)\s*(?:of)?\s*[:\-]?\s*([^\n]+?)(?=facult|school\s+of|college\s+of|\n\n|\Z)",
    re.IGNORECASE | re.DOTALL,
)

_DEPARTMENT_BLOCK_PATTERN = re.compile(
    r"(?:departments?|programmes?|programs?|courses?)\s*(?:offered|available)?\s*[:\-]?\s*([^\n]+(?:\n[^\n]+){0,40})",
    re.IGNORECASE,
)

_DEGREE_TOKENS = [
    "B.Sc", "BSc", "B.A", "BA", "B.Eng", "BEng", "B.Tech", "BTech",
    "B.Ed", "BEd", "B.Pharm", "B.Agric", "B.Med", "B.NSc",
    "MBBS", "LL.B", "LLB", "DVM",
    "ND", "HND", "NCE",
    "Bachelor of",
]

_DURATION_PATTERNS = [
    r"(\d)\s*(?:years?|yrs?)",
    r"(\d)\s*(?:sessions?)",
]


def _split_list(s: str) -> list[str]:
    parts = re.split(r"[,;\n]|(?:\d+\.|\u2022|\*|\-)\s+", s)
    filtered: list[str] = []
    for p in parts:
        p = p.strip(" .:;")
        if not p or len(p) <= 2:
            continue
        if re.search(r"[₦\u20a6]|[\/\\]?\d[\d,]+\s*(?:naira|ngn)", p, re.IGNORECASE):
            continue
        if re.match(r"^\d{1,3}[,.]?\d{3,}(\.\d+)?$", p):
            continue
        filtered.append(p)
    return filtered


def _detect_degree(line: str) -> tuple[str | None, str | None]:
    line_low = line.lower()
    if "nd" in line_low and re.search(r"\bnd\b", line_low):
        return "ND", "ND"
    if "hnd" in line_low:
        return "HND", "HND"
    if "nce" in line_low:
        return "NCE", "NCE"
    if "mbbs" in line_low:
        return "MBBS", "undergraduate"
    if re.search(r"\bll\.?b\b", line_low):
        return "LL.B", "undergraduate"
    if "b.eng" in line_low or "beng" in line_low:
        return "B.Eng", "undergraduate"
    if "b.tech" in line_low or "btech" in line_low:
        return "B.Tech", "undergraduate"
    if "b.ed" in line_low or "bed" in line_low:
        return "B.Ed", "undergraduate"
    if "b.pharm" in line_low or "pharm" in line_low:
        return "B.Pharm", "undergraduate"
    if "b.sc" in line_low or "bsc" in line_low:
        return "B.Sc", "undergraduate"
    if "b.a" in line_low and re.search(r"\bb\.a\b", line_low):
        return "B.A", "undergraduate"
    if "bachelor of science" in line_low:
        return "B.Sc", "undergraduate"
    if "bachelor of arts" in line_low:
        return "B.A", "undergraduate"
    if "bachelor of engineering" in line_low:
        return "B.Eng", "undergraduate"
    return None, None


def _extract_duration(line: str) -> int | None:
    for pat in _DURATION_PATTERNS:
        m = re.search(pat, line, re.IGNORECASE)
        if m:
            try:
                v = int(m.group(1))
                if 1 <= v <= 8:
                    return v
            except ValueError:
                continue
    return None


def parse_programs(text: str, inst_type: InstitutionType) -> tuple[list[str], list[Program]]:
    """Return (faculties, programs)."""
    faculties: list[str] = []
    for m in _FACULTIES_PATTERN.finditer(text):
        chunk = m.group(1)
        for item in _split_list(chunk):
            item = re.sub(r"^(?:Faculty|School|College)\s+(?:of\s+)?", "", item, flags=re.IGNORECASE).strip()
            if item and len(item) < 80:
                if item.title() not in faculties:
                    faculties.append(item.title())

    programs: list[Program] = []
    seen: set[str] = set()

    # Parse structured "course: duration" or "course (X years)" lines
    for line in text.split("\n"):
        line = line.strip(" -•\t*#")
        line = re.sub(r"^#{1,6}\s+", "", line)
        if len(line) < 4 or len(line) > 200:
            continue
        # Skip fee-row noise: lines dominated by numbers/currency
        digits_ratio = sum(1 for ch in line if ch.isdigit()) / max(len(line), 1)
        if digits_ratio > 0.5 or re.search(r"[₦\u20a6]\s*\d", line):
            continue
        if re.match(r"^\d+[\s,]?(\d{3}|0{3})", line.strip()):
            continue
        name_match = re.match(
            r"^([A-Z][A-Za-z0-9\s&/\-\(\),\.]{2,80}?)\s*(?:\((\d)\s*years?\)|:\s*\d|\s+\d\s*years?)",
            line,
        )
        name = None
        duration = _extract_duration(line)
        if name_match:
            name = name_match.group(1).strip(" ,.;")
            name = re.sub(r"\s+", " ", name)
        else:
            # Cheap heuristic: a line that mentions a known degree token
            for tok in _DEGREE_TOKENS:
                if re.search(r"\b" + re.escape(tok) + r"\b", line, re.IGNORECASE):
                    clean = re.sub(r"\s+", " ", line).strip(" .,;:").strip()
                    if 4 <= len(clean) <= 120:
                        name = clean
                    break
        if not name:
            continue
        degree, level = _detect_degree(line)
        if not level and inst_type == InstitutionType.POLYTECHNIC:
            level = "ND"
            degree = "ND"
        if not level and inst_type == InstitutionType.COLLEGE_OF_EDUCATION:
            level = "NCE"
            degree = "NCE"
        if not level and inst_type == InstitutionType.UNIVERSITY:
            level = "undergraduate"
        key = (name.lower(), level or "")
        if key in seen:
            continue
        seen.add(key)
        # faculty heuristic
        faculty = None
        if faculties:
            for f in faculties:
                if f.lower() in name.lower() or name.lower() in f.lower():
                    faculty = f
                    break
        programs.append(
            Program(
                name=name,
                faculty=faculty,
                degree=degree,
                level=level,
                duration_years=duration,
                affiliated_university=None,
            )
        )
        if len(programs) >= 100:
            break

    return faculties, programs
