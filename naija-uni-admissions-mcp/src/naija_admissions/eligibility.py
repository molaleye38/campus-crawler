"""Eligibility rules — pure functions for the Campus Compass Intelligence Core (CCIC).

Reads structured cut-off + catchment data from the KB and returns a structured
decision that GLM (or any report generator) can turn into a human-readable report.

Example:
    from naija_admissions.eligibility import check_eligibility, StudentProfile
    from naija_admissions.writers.kb_schema import connect_kb

    conn = connect_kb("data/institutions.db")
    decision = check_eligibility(conn, student=StudentProfile(
        course="Medicine and Surgery",
        institution="University of Ibadan",
        jamb_score=275,
        olevel_subjects=["English","Mathematics","Biology","Chemistry","Physics"],
        olevel_credits=5,
        olevel_sittings=1,
        state_of_origin="Oyo",
        post_utme_score=72,
    ))
    print(decision.eligible, decision.reasons)
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StudentProfile:
    course: str
    institution: str
    jamb_score: int
    olevel_subjects: list[str]
    olevel_credits: int
    olevel_sittings: int = 1
    state_of_origin: str | None = None
    post_utme_score: int | None = None
    awaiting_result: bool = False
    academic_year: str = "2025/2026"
    aggregate_score: float | None = None


@dataclass
class EligibilityDecision:
    eligible: bool
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    aggregate_score: float | None = None
    merit_cutoff: float | None = None
    catchment_cutoff: float | None = None
    elds_cutoff: float | None = None
    catchment_applies: bool = False
    elds_applies: bool = False
    checked_against: str = ""
    alternative_programs: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "eligible": self.eligible,
            "reasons": self.reasons,
            "warnings": self.warnings,
            "aggregate_score": self.aggregate_score,
            "merit_cutoff": self.merit_cutoff,
            "catchment_cutoff": self.catchment_cutoff,
            "elds_cutoff": self.elds_cutoff,
            "catchment_applies": self.catchment_applies,
            "elds_applies": self.elds_applies,
            "checked_against": self.checked_against,
            "alternative_programs": self.alternative_programs,
        }


_ELDS_STATES = {
    "Adamawa","Bauchi","Bayelsa","Benue","Borno","Cross River","Gombe","Jigawa",
    "Kaduna","Kano","Katsina","Kebbi","Kogi","Kwara","Nasarawa","Niger","Plateau",
    "Rivers","Sokoto","Taraba","Yobe","Zamfara",
}


def _row_to_dict(row: sqlite3.Row | tuple | None) -> dict[str, Any] | None:
    if row is None:
        return None
    if isinstance(row, sqlite3.Row):
        return dict(row)
    return None


def _tuple_to_dict(row: tuple, cols: list[str]) -> dict[str, Any]:
    return dict(zip(cols, row, strict=False))


_ADM_REQ_COLS = [
    "id", "institution_id", "program_id", "olevel_subjects_json",
    "olevel_credits_min", "utme_subjects_json", "minimum_jamb",
    "minimum_credits", "awaiting_result_accepted",
    "max_olevel_sittings", "direct_entry_requirements",
    "post_utme_required", "post_utme_format",
    "post_utme_weight_pct", "aggregate_formula",
]

_CUTOFF_COLS = [
    "id", "institution_id", "program_id", "academic_year",
    "merit_cutoff", "departmental_cutoff", "catchment_cutoff",
    "elds_cutoff", "aggregate_formula", "source_url", "crawl_date",
]

_CATCHMENT_COLS = [
    "id", "institution_id", "name", "eligible_states_json", "policy", "details",
]


def _get_institution_id(conn: sqlite3.Connection, name: str) -> int | None:
    row = conn.execute(
        "SELECT id FROM kb_institutions WHERE name = ? OR short_name = ?",
        (name, name),
    ).fetchone()
    return int(row[0]) if row else None


def _get_program_id(conn: sqlite3.Connection, institution_id: int, course: str) -> int | None:
    row = conn.execute(
        "SELECT id FROM kb_programs WHERE institution_id = ? AND name LIKE ?",
        (institution_id, f"%{course}%"),
    ).fetchone()
    return int(row[0]) if row else None


def _get_requirements(
    conn: sqlite3.Connection, institution_id: int, program_id: int | None
) -> dict[str, Any] | None:
    if program_id is not None:
        row = conn.execute(
            "SELECT * FROM kb_admission_requirements WHERE institution_id = ? AND program_id = ?",
            (institution_id, program_id),
        ).fetchone()
    if program_id is None or row is None:
        row = conn.execute(
            "SELECT * FROM kb_admission_requirements "
            "WHERE institution_id = ? AND program_id IS NULL",
            (institution_id,),
        ).fetchone()
    if row is None:
        return None
    if isinstance(row, sqlite3.Row):
        d = dict(row)
    else:
        d = _tuple_to_dict(row, _ADM_REQ_COLS)
    for k in ("olevel_subjects_json", "utme_subjects_json"):
        if d.get(k):
            try:
                d[k.replace("_json", "")] = json.loads(d[k])
            except (ValueError, TypeError):
                d[k.replace("_json", "")] = []
        else:
            d[k.replace("_json", "")] = []
    return d


def _get_cutoff(
    conn: sqlite3.Connection,
    institution_id: int,
    program_id: int | None,
    academic_year: str,
) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM kb_cutoff_marks "
        "WHERE institution_id = ? AND COALESCE(program_id, -1) = COALESCE(?, -1) "
        "AND academic_year = ?",
        (institution_id, program_id, academic_year),
    ).fetchone()
    return dict(row) if isinstance(row, sqlite3.Row) else _tuple_to_dict(row, _CUTOFF_COLS) if row else None


def _get_catchment(conn: sqlite3.Connection, institution_id: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM kb_catchment_areas WHERE institution_id = ?",
        (institution_id,),
    ).fetchall()
    out = []
    for r in rows:
        if isinstance(r, sqlite3.Row):
            d = dict(r)
        else:
            d = _tuple_to_dict(r, _CATCHMENT_COLS)
        if d.get("eligible_states_json"):
            try:
                d["eligible_states"] = json.loads(d["eligible_states_json"])
            except (ValueError, TypeError):
                d["eligible_states"] = []
        else:
            d["eligible_states"] = []
        out.append(d)
    return out


def _compute_aggregate(
    requirements: dict[str, Any] | None, jamb: int, post_utme: int | None
) -> float | None:
    if requirements is None:
        return None
    formula = (requirements.get("aggregate_formula") or "").lower()
    has_utme_term = "utme/8" in formula or "utme / 8" in formula or "jamb/8" in formula
    has_post_term = (
        "post-utme" in formula or "post utme" in formula or "postutme" in formula
    )
    if has_utme_term and has_post_term and post_utme is not None:
        return round((jamb / 8) + (post_utme / 2), 4)
    if has_utme_term:
        return round(jamb / 8, 4)
    return None


def _is_elds_state(state: str | None) -> bool:
    if not state:
        return False
    return state.strip().title() in _ELDS_STATES


def _check_olevel(student: StudentProfile, req: dict[str, Any] | None) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if req is None:
        return True, ["No O-Level requirements recorded — skipping O-Level check."]
    required_subjects = req.get("olevel_subjects") or []
    if required_subjects:
        missing = [s for s in required_subjects if s not in student.olevel_subjects]
        if missing:
            reasons.append(f"Missing required O-Level subjects: {', '.join(missing)}")
            return False, reasons
    min_credits = req.get("olevel_credits_min") or req.get("minimum_credits")
    if min_credits and student.olevel_credits < min_credits:
        reasons.append(
            f"O-Level credits {student.olevel_credits} below minimum {min_credits}"
        )
        return False, reasons
    max_sittings = req.get("max_olevel_sittings")
    if max_sittings and student.olevel_sittings > max_sittings:
        reasons.append(
            f"O-Level sittings {student.olevel_sittings} exceed maximum {max_sittings}"
        )
        return False, reasons
    if student.awaiting_result and req.get("awaiting_result_accepted") == 0:
        reasons.append("Awaiting results not accepted by this programme")
        return False, reasons
    reasons.append("O-Level requirements met")
    return True, reasons


def _check_utme(student: StudentProfile, req: dict[str, Any] | None) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if req is None:
        return True, ["No UTME requirements recorded — skipping UTME check."]
    minimum_jamb = req.get("minimum_jamb")
    if minimum_jamb and student.jamb_score < minimum_jamb:
        reasons.append(f"JAMB {student.jamb_score} below minimum {minimum_jamb}")
        return False, reasons
    required_subjects = req.get("utme_subjects") or []
    if required_subjects:
        reasons.append(
            f"Confirm UTME subjects match required: {', '.join(required_subjects)}"
        )
    reasons.append("JAMB score above minimum")
    return True, reasons


def _check_post_utme(
    student: StudentProfile, req: dict[str, Any] | None
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if req is None:
        return True, ["No Post-UTME info recorded."]
    if req.get("post_utme_required") == 1 and student.post_utme_score is None:
        reasons.append("Post-UTME required but no score provided")
        return False, reasons
    reasons.append("Post-UTME check passed")
    return True, reasons


def _check_cutoff(
    student: StudentProfile,
    cutoff: dict[str, Any] | None,
    catchment_rows: list[dict[str, Any]],
) -> tuple[bool, list[str], EligibilityDecision]:
    decision = EligibilityDecision(eligible=True)
    reasons: list[str] = []
    if cutoff is None:
        reasons.append("No cut-off mark recorded for this course/year — cannot finalize eligibility.")
        decision.eligible = False
        decision.reasons = reasons
        return False, reasons, decision
    merit = cutoff.get("merit_cutoff")
    catch = cutoff.get("catchment_cutoff")
    elds = cutoff.get("elds_cutoff")
    decision.merit_cutoff = merit
    decision.catchment_cutoff = catch
    decision.elds_cutoff = elds

    is_elds = _is_elds_state(student.state_of_origin)
    is_catchment = any(
        student.state_of_origin in (c.get("eligible_states") or [])
        for c in catchment_rows
        if c.get("policy", "").lower() == "geographical"
    )
    decision.catchment_applies = is_catchment
    decision.elds_applies = is_elds

    if student.aggregate_score is None:
        reasons.append("No aggregate score available — cannot compare to cut-off.")
        decision.eligible = False
        decision.reasons = reasons
        return False, reasons, decision

    cut_to_use = merit
    policy_used = "merit"
    if is_catchment and catch is not None and catch < (merit or 999):
        cut_to_use = catch
        policy_used = "catchment"
    elif is_elds and elds is not None and elds < (merit or 999):
        cut_to_use = elds
        policy_used = "elds"

    if student.aggregate_score >= (cut_to_use or 0):
        reasons.append(
            f"Aggregate {student.aggregate_score:.3f} meets {policy_used} cut-off {cut_to_use}"
        )
    else:
        reasons.append(
            f"Aggregate {student.aggregate_score:.3f} below {policy_used} cut-off {cut_to_use}"
        )
        decision.eligible = False
    decision.reasons = reasons
    return decision.eligible, reasons, decision


def _find_alternatives(
    conn: sqlite3.Connection, student: StudentProfile, max_results: int = 5
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT c.merit_cutoff, p.name AS programme, i.name AS institution
        FROM kb_cutoff_marks c
        LEFT JOIN kb_programs p ON p.id = c.program_id
        JOIN kb_institutions i ON i.id = c.institution_id
        WHERE c.academic_year = ?
          AND c.merit_cutoff IS NOT NULL
          AND (p.name LIKE ? OR p.name LIKE ?)
          AND i.name != ?
        ORDER BY ABS(c.merit_cutoff - ?) ASC
        LIMIT ?
        """,
        (
            student.academic_year,
            f"%{student.course.split(' ')[0]}%",
            f"%{student.course}%",
            student.institution,
            student.aggregate_score or 100,
            max_results,
        ),
    ).fetchall()
    out = []
    for r in rows:
        out.append({
            "programme": r[1] or "(unknown)",
            "institution": r[2],
            "merit_cutoff": r[0],
        })
    return out


def check_eligibility(
    conn: sqlite3.Connection, *, student: StudentProfile
) -> EligibilityDecision:
    inst_id = _get_institution_id(conn, student.institution)
    if inst_id is None:
        return EligibilityDecision(
            eligible=False,
            reasons=[f"Institution '{student.institution}' not found in knowledge base"],
        )
    prog_id = _get_program_id(conn, inst_id, student.course)
    if prog_id is None:
        return EligibilityDecision(
            eligible=False,
            reasons=[f"Programme '{student.course}' not found at '{student.institution}'"],
        )
    req_inst = _get_requirements(conn, inst_id, None)
    req_prog = _get_requirements(conn, inst_id, prog_id)
    req = req_prog or req_inst
    cutoff = _get_cutoff(conn, inst_id, prog_id, student.academic_year)
    catchment_rows = _get_catchment(conn, inst_id)

    aggregate = _compute_aggregate(req, student.jamb_score, student.post_utme_score)
    student_with_aggregate = StudentProfile(**{**student.__dict__, "aggregate_score": aggregate})

    ok_olevel, why_olevel = _check_olevel(student, req)
    ok_utme, why_utme = _check_utme(student, req)
    ok_post, why_post = _check_post_utme(student, req)
    ok_cut, why_cut, cut_decision = _check_cutoff(student_with_aggregate, cutoff, catchment_rows)

    ineligible_reasons: list[str] = []
    if not ok_olevel:
        ineligible_reasons.extend(why_olevel)
    if not ok_utme:
        ineligible_reasons.extend(why_utme)
    if not ok_post:
        ineligible_reasons.extend(why_post)
    if not ok_cut:
        ineligible_reasons.extend(why_cut)

    all_reasons = why_olevel + why_utme + why_post + why_cut
    eligible = ok_olevel and ok_utme and ok_post and ok_cut

    alts: list[dict[str, Any]] = []
    if not eligible:
        alts = _find_alternatives(conn, student_with_aggregate)

    return EligibilityDecision(
        eligible=eligible,
        reasons=all_reasons,
        warnings=[],
        aggregate_score=aggregate,
        merit_cutoff=cut_decision.merit_cutoff,
        catchment_cutoff=cut_decision.catchment_cutoff,
        elds_cutoff=cut_decision.elds_cutoff,
        catchment_applies=cut_decision.catchment_applies,
        elds_applies=cut_decision.elds_applies,
        checked_against=f"{student.institution} / {student.course} / {student.academic_year}",
        alternative_programs=alts,
    )
