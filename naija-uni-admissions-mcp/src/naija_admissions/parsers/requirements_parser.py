"""Parser for admission requirements (UTME, O-level, Post-UTME, direct entry).

Type-aware cutoff ranges:
- Universities: UTME cutoff typically 180-260
- Polytechnics: UTME cutoff typically 120-150
- Colleges of Education: UTME cutoff typically 100-120
"""

from __future__ import annotations

import re

from ..models import AdmissionRequirements, CutoffEntry, InstitutionType, PostUTME

CUTOFF_RANGES: dict[InstitutionType, tuple[int, int]] = {
    InstitutionType.UNIVERSITY: (150, 280),
    InstitutionType.POLYTECHNIC: (90, 180),
    InstitutionType.COLLEGE_OF_EDUCATION: (70, 150),
}


_CUTOFF_PATTERNS = [
    r"(?:utme|jamb)\s*(?:cut[-\s]?off(?:\s*mark)?|score)\s*(?:[:\-]?\s*|\s+is\s+)\s*(\d{2,3})",
    r"cut[-\s]?off\s*(?:mark)?\s*(?:[:\-]?\s*|\s+is\s+)\s*(\d{2,3})",
    r"(\d{3})\s*(?:is\s+)?(?:the\s+)?(?:minimum\s+)?(?:utme|jamb|cut[-\s]?off)",
    r"minimum\s+(?:utme|jamb)\s+(?:score|cut[-\s]?off)\s*(?:of|:)?\s*(\d{3})",
    r"\b(\d{3})\b\s+(?:in\s+)?(?:utme|jamb)",
]

_OLEVEL_SUBJECTS_PATTERNS = [
    r"o[\\s-]?level\s*(?:subjects?|requirements?)\s*[:\-]?\s*([^.]+)",
    r"ssce\s*(?:subjects?|requirements?)\s*[:\-]?\s*([^.]+)",
    r"waec\s*(?:subjects?|requirements?)\s*[:\-]?\s*([^.]+)",
    r"five\s*\(?\s*5?\s*\)?\s*(?:credit\s+)?(?:passes?|subjects?)\s*(?:in|including|:)?\s*([^.]+)",
]

_CREDITS_PATTERNS = [
    r"(\d)\s*credit\s*passes",
    r"minimum\s*of\s*(\d)\s*credits",
    r"at\s*least\s*(\d)\s*credit",
    r"five\s*\(?5\)?\s*credit",
]

_UTME_SUBJECTS_PATTERNS = [
    r"utme\s*subjects?\s*[:\-]?\s*([^.]+)",
    r"jamb\s*subjects?\s*[:\-]?\s*([^.]+)",
    r"jamb\s*subject\s*combination\s*[:\-]?\s*([^.]+)",
]

_POST_UTME_PATTERNS = [
    r"post[-\s]?utme\s*(?:screening)?\s*[:\-]?\s*([^.]+)",
    r"post[-\s]?jamb\s*(?:screening)?\s*[:\-]?\s*([^.]+)",
    r"screening\s*exercise\s*[:\-]?\s*([^.]+)",
]

_DE_PATTERNS = [
    r"direct\s*entry\s*(?:requirements?|qualifications?)\s*[:\-]?\s*([^.]+(?:\.[^.]+){0,3})",
    r"\bde\b\s*requirements?\s*[:\-]?\s*([^.]+)",
]

_PER_COURSE_PATTERN = re.compile(
    r"(?P<course>[A-Z][A-Za-z\s&/\-]{1,60}?)\s*[:\-]\s*(\d{3})\b",
    re.MULTILINE,
)


def _find_first(patterns: list[str], text: str) -> str | None:
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m:
            try:
                return m.group(1).strip()
            except IndexError:
                continue
    return None


def _split_subjects(s: str | None) -> list[str]:
    if not s:
        return []
    parts = re.split(r"[,;/]|\band\b", s, flags=re.IGNORECASE)
    return [p.strip(" .:;") for p in parts if p.strip(" .:;")]


def _extract_cutoff(text: str, inst_type: InstitutionType) -> int | None:
    lo, hi = CUTOFF_RANGES[inst_type]
    for pat in _CUTOFF_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE | re.MULTILINE):
            try:
                v = int(m.group(1))
            except (ValueError, IndexError):
                continue
            if lo <= v <= hi:
                return v
    return None


def _extract_per_course_cutoffs(text: str, inst_type: InstitutionType) -> list[CutoffEntry] | None:
    lo, hi = CUTOFF_RANGES[inst_type]
    found: list[CutoffEntry] = []
    seen: set[str] = set()
    for m in _PER_COURSE_PATTERN.finditer(text):
        course = m.group(1).strip().title()
        try:
            v = int(m.group(2))
        except ValueError:
            continue
        if lo <= v <= hi and course.lower() not in seen:
            seen.add(course.lower())
            found.append(CutoffEntry(course=course, cutoff=v))
    return found[:50] or None


def _extract_post_utme(text: str) -> PostUTME | None:
    s = _find_first(_POST_UTME_PATTERNS, text)
    if not s:
        return None
    required = True
    if re.search(r"\bnot\s+(?:required|conducted)\b", s, re.IGNORECASE):
        required = False
    weight_match = re.search(r"(\d{1,2})\s*%\s*(?:of|weight|score)?", s)
    weight = int(weight_match.group(1)) if weight_match else None
    fmt = None
    if re.search(r"\bexamination?\b", s, re.IGNORECASE):
        fmt = "examination"
    elif re.search(r"\bscreening\b", s, re.IGNORECASE):
        fmt = "screening"
    return PostUTME(required=required, format=fmt, weight_pct=weight)


def parse_requirements(text: str, inst_type: InstitutionType) -> AdmissionRequirements:
    olevel = _split_subjects(_find_first(_OLEVEL_SUBJECTS_PATTERNS, text))
    utme = _split_subjects(_find_first(_UTME_SUBJECTS_PATTERNS, text))
    cutoff = _extract_cutoff(text, inst_type)
    per_course = _extract_per_course_cutoffs(text, inst_type)
    post = _extract_post_utme(text)
    de = _find_first(_DE_PATTERNS, text)

    credits_min = None
    cs = _find_first(_CREDITS_PATTERNS, text)
    if cs:
        try:
            credits_min = int(cs)
        except ValueError:
            pass

    return AdmissionRequirements(
        olevel_subjects=olevel,
        olevel_credits_min=credits_min,
        utme_subjects=utme,
        utme_cutoff_general=cutoff,
        utme_cutoff_per_course=per_course,
        post_utme=post,
        direct_entry_requirements=de,
    )
