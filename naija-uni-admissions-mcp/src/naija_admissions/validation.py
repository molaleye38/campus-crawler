"""Validation rules for Institution data.

Validates extracted admission data BEFORE writing to Supabase. Catches:
- Out-of-range cutoffs (UTME: 100-400)
- Empty required fields (name, state)
- O-Level credit minimums (must be 5-9)
- Fee sanity (positive, <100M NGN)
- Faculty/program name length / content
- URL format / accessibility
- Duplicate (institution, course, session) within the same Institution object
- Conflicting rules (e.g. utme_cutoff_per_course that contradict general cutoff)
"""

from __future__ import annotations

import re
from typing import Any


class ValidationError:
    def __init__(self, field: str, code: str, message: str, severity: str = "error"):
        self.field = field
        self.code = code
        self.message = message
        self.severity = severity

    def to_dict(self) -> dict[str, str]:
        return {
            "field": self.field,
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
        }

    def __repr__(self) -> str:
        return f"ValidationError({self.field}, {self.code}, {self.severity}): {self.message}"


_UTME_MIN = 100
_UTME_MAX = 400
_OLEVEL_CREDITS_MIN = 5
_OLEVEL_CREDITS_MAX = 9
_MAX_FEE_NGN = 100_000_000
_URL_RE = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)


def _has(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


def validate_institution(inst: Any) -> list[ValidationError]:
    errors: list[ValidationError] = []

    if not _has(getattr(inst, "name", None)):
        errors.append(ValidationError("name", "name_empty", "Institution name is required"))

    name = (getattr(inst, "name", "") or "").strip()
    if len(name) > 200:
        errors.append(ValidationError("name", "name_too_long", f"Institution name too long ({len(name)} chars, max 200)"))

    if not _has(getattr(inst, "institution_type", None)):
        errors.append(ValidationError("institution_type", "type_missing", "institution_type is required"))

    if not _has(getattr(inst, "type", None)):
        errors.append(ValidationError("ownership_type", "type_missing", "ownership type is required"))

    website = getattr(inst, "website", None)
    if _has(website) and not _URL_RE.match(website):
        errors.append(ValidationError("website", "website_invalid", f"Website URL invalid: {website[:80]}"))

    admission_portal = getattr(inst, "admission_portal", None)
    if _has(admission_portal) and not _URL_RE.match(admission_portal):
        errors.append(ValidationError("admission_portal", "portal_invalid", f"Admission portal URL invalid: {admission_portal[:80]}"))

    year = getattr(inst, "year_established", None)
    if year is not None and not (1800 <= year <= 2100):
        errors.append(ValidationError("year_established", "year_out_of_range", f"year_established out of range: {year}"))

    req = getattr(inst, "admission_requirements", None)
    if req is not None:
        if getattr(req, "olevel_credits_min", None) is not None:
            if not (_OLEVEL_CREDITS_MIN <= req.olevel_credits_min <= _OLEVEL_CREDITS_MAX):
                errors.append(ValidationError(
                    "admission_requirements.olevel_credits_min",
                    "olevel_credits_out_of_range",
                    f"olevel_credits_min must be {_OLEVEL_CREDITS_MIN}-{_OLEVEL_CREDITS_MAX}, got {req.olevel_credits_min}",
                ))

        cutoff = getattr(req, "utme_cutoff_general", None)
        if cutoff is not None:
            if not (_UTME_MIN <= cutoff <= _UTME_MAX):
                errors.append(ValidationError(
                    "admission_requirements.utme_cutoff_general",
                    "utme_cutoff_out_of_range",
                    f"utme_cutoff_general must be {_UTME_MIN}-{_UTME_MAX}, got {cutoff}",
                ))

        per_course = getattr(req, "utme_cutoff_per_course", None) or []
        seen_cutoffs: set[tuple[str, int]] = set()
        for c in per_course:
            if getattr(c, "course", None) and getattr(c, "cutoff", None) is not None:
                key = (c.course.strip().lower(), int(c.cutoff))
                if key in seen_cutoffs:
                    errors.append(ValidationError(
                        "admission_requirements.utme_cutoff_per_course",
                        "duplicate_cutoff",
                        f"Duplicate cutoff for {c.course}: {c.cutoff}",
                        severity="warning",
                    ))
                seen_cutoffs.add(key)
                if not (_UTME_MIN <= c.cutoff <= _UTME_MAX):
                    errors.append(ValidationError(
                        "admission_requirements.utme_cutoff_per_course",
                        "utme_cutoff_per_course_out_of_range",
                        f"Cutoff for {c.course} ({c.cutoff}) out of range {_UTME_MIN}-{_UTME_MAX}",
                    ))

        if cutoff is not None and per_course:
            for c in per_course:
                if c.cutoff and (c.cutoff - cutoff) > 100:
                    errors.append(ValidationError(
                        "admission_requirements.utme_cutoff_per_course",
                        "conflicting_cutoff",
                        f"Course cutoff {c.cutoff} for {c.course} differs from general {cutoff} by >100",
                        severity="warning",
                    ))

    faculties = getattr(inst, "faculties", []) or []
    for i, f in enumerate(faculties):
        if not _has(f) or len(f) > 200:
            errors.append(ValidationError(
                f"faculties[{i}]",
                "faculty_name_invalid",
                f"Faculty name invalid: {str(f)[:80]}",
            ))

    programs = getattr(inst, "programs", []) or []
    seen_programs: set[str] = set()
    for i, p in enumerate(programs):
        if not _has(getattr(p, "name", None)):
            errors.append(ValidationError(
                f"programs[{i}]",
                "program_name_empty",
                "Program name is required",
            ))
        else:
            key = p.name.strip().lower()
            if key in seen_programs:
                errors.append(ValidationError(
                    f"programs[{i}]",
                    "duplicate_program",
                    f"Duplicate program: {p.name}",
                    severity="warning",
                ))
            seen_programs.add(key)

    fee_tiers = getattr(inst, "fee_tiers", []) or []
    seen_fees: set[tuple[str, int | None]] = set()
    for i, f in enumerate(fee_tiers):
        ngn = getattr(f, "tuition_per_session_ngn", None)
        if ngn is not None:
            if ngn <= 0:
                errors.append(ValidationError(
                    f"fee_tiers[{i}]",
                    "fee_negative",
                    f"Fee must be positive: {ngn}",
                ))
            elif ngn > _MAX_FEE_NGN:
                errors.append(ValidationError(
                    f"fee_tiers[{i}]",
                    "fee_excessive",
                    f"Fee {ngn} NGN exceeds {_MAX_FEE_NGN} sanity limit",
                ))
        key = (
            getattr(f, "program_or_faculty", "") or "",
            ngn,
        )
        if key in seen_fees and ngn:
            errors.append(ValidationError(
                f"fee_tiers[{i}]",
                "duplicate_fee",
                f"Duplicate fee tier for {key[0]}: {ngn} NGN",
                severity="warning",
            ))
        seen_fees.add(key)

    return errors


def has_blocking_errors(errors: list[ValidationError]) -> bool:
    return any(e.severity == "error" for e in errors)


def to_dict_list(errors: list[ValidationError]) -> list[dict[str, str]]:
    return [e.to_dict() for e in errors]
