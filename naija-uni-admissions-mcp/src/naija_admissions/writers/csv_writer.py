"""CSV writers — institutions.csv, programs.csv, fees.csv."""

from __future__ import annotations

import csv
from pathlib import Path

from ..models import Institution


def write_institutions_csv(path: str | Path, institutions: list[Institution]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    headers = [
        "name", "short_name", "institution_type", "type", "state", "city",
        "website", "year_established",
        "utme_cutoff_general", "olevel_credits_min", "post_utme_required",
        "application_portal_url", "application_fee_ngn", "acceptance_fee_ngn",
        "faculties_count", "programs_count", "fee_tiers_count",
        "catchment_policy",
        "confidence_overall",
        "last_updated",
    ]
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for inst in institutions:
            req = inst.admission_requirements
            app = inst.application_process
            cat = inst.catchment_areas[0] if inst.catchment_areas else None
            w.writerow([
                inst.name,
                inst.short_name or "",
                inst.institution_type.value if hasattr(inst.institution_type, "value") else inst.institution_type,
                inst.type.value if hasattr(inst.type, "value") else inst.type,
                inst.state or "",
                inst.city or "",
                inst.website or "",
                inst.year_established or "",
                req.utme_cutoff_general if req else "",
                req.olevel_credits_min if req else "",
                (req.post_utme.required if req and req.post_utme else ""),
                (app.portal_url if app else ""),
                (app.application_fee_ngn if app else ""),
                (app.acceptance_fee_ngn if app else ""),
                len(inst.faculties),
                len(inst.programs),
                len(inst.fee_tiers),
                (cat.policy.value if cat and hasattr(cat.policy, "value") else (cat.policy if cat else "")),
                inst.confidence.get("overall", ""),
                inst.last_updated,
            ])


def write_programs_csv(path: str | Path, institutions: list[Institution]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    headers = ["institution_name", "program_name", "faculty", "degree", "level", "duration_years", "affiliated_university"]
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for inst in institutions:
            for prog in inst.programs:
                w.writerow([
                    inst.name,
                    prog.name,
                    prog.faculty or "",
                    prog.degree or "",
                    prog.level or "",
                    prog.duration_years or "",
                    prog.affiliated_university or "",
                ])


def write_fees_csv(path: str | Path, institutions: list[Institution]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    headers = [
        "institution_name", "program_or_faculty", "tuition_per_session_ngn",
        "tuition_per_session_usd", "currency", "indigene", "non_indigene",
        "source_url", "fee_year",
    ]
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for inst in institutions:
            for f_tier in inst.fee_tiers:
                ind = ""
                nind = ""
                if f_tier.indigene_vs_non_indigene:
                    ind = f_tier.indigene_vs_non_indigene.get("indigene", "")
                    nind = f_tier.indigene_vs_non_indigene.get("non_indigene", "")
                w.writerow([
                    inst.name,
                    f_tier.program_or_faculty,
                    f_tier.tuition_per_session_ngn or "",
                    f_tier.tuition_per_session_usd or "",
                    f_tier.currency,
                    ind,
                    nind,
                    f_tier.source_url,
                    f_tier.fee_year or "",
                ])
