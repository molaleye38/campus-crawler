"""Pydantic models for the Naija Admissions pipeline.

The schema is a single `Institution` model discriminated by `institution_type`.
Universities, polytechnics, and colleges of education share the same shape;
some fields (catchment_areas, application_process) are mostly empty for
non-university types.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class InstitutionType(StrEnum):
    UNIVERSITY = "university"
    POLYTECHNIC = "polytechnic"
    COLLEGE_OF_EDUCATION = "college_of_education"
    NURSING_SCHOOL = "nursing_school"
    COLLEGE_OF_HEALTH_TECHNOLOGY = "college_of_health_technology"
    INNOVATION_ENTERPRISE_INSTITUTION = "innovation_enterprise_institution"
    MONOTECHNIC = "monotechnic"


class OwnershipType(StrEnum):
    FEDERAL = "federal"
    STATE = "state"
    PRIVATE = "private"


class CatchmentPolicy(StrEnum):
    ELDS = "ELDS"
    GEOGRAPHICAL = "geographical"
    NONE = "none"


class CatchmentArea(BaseModel):
    name: str
    details: str | None = None
    policy: CatchmentPolicy = CatchmentPolicy.NONE


class Program(BaseModel):
    name: str
    faculty: str | None = None
    degree: str | None = Field(
        default=None,
        description="B.Sc|B.A|B.Eng|MBBS|LL.B|ND|HND|NCE|B.Ed|other",
    )
    level: str | None = Field(
        default=None,
        description="undergraduate | ND | HND | NCE — disambiguates polytechnic/COE progression",
    )
    duration_years: int | None = None
    affiliated_university: str | None = Field(
        default=None,
        description="COE programs granting a B.Ed via affiliation with a university",
    )


class FeeTier(BaseModel):
    program_or_faculty: str = Field(default="general")
    tuition_per_session_ngn: int | None = None
    tuition_per_session_usd: int | None = None
    currency: str = "NGN"
    indigene_vs_non_indigene: dict[str, int] | None = None
    source_url: str
    fee_year: int | None = None


class PostUTME(BaseModel):
    required: bool | None = None
    format: str | None = None
    weight_pct: int | None = None


class CutoffEntry(BaseModel):
    course: str
    cutoff: int


class AdmissionRequirements(BaseModel):
    olevel_subjects: list[str] = Field(default_factory=list)
    olevel_credits_min: int | None = None
    utme_subjects: list[str] = Field(default_factory=list)
    utme_cutoff_general: int | None = Field(
        default=None,
        description="Universities ~180+, polytechnics ~120-150, COEs ~100-120",
    )
    utme_cutoff_per_course: list[CutoffEntry] | None = None
    post_utme: PostUTME | None = None
    direct_entry_requirements: str | None = None


class ApplicationProcess(BaseModel):
    steps: list[str] = Field(default_factory=list)
    portal_url: str | None = None
    application_fee_ngn: int | None = None
    acceptance_fee_ngn: int | None = None
    deadlines: str | None = None


class Source(BaseModel):
    url: str
    provider: str = "firecrawl"
    accessed_on: str = Field(default_factory=lambda: datetime.utcnow().date().isoformat())


class Institution(BaseModel):
    institution_type: InstitutionType
    name: str
    short_name: str | None = None
    type: OwnershipType
    state: str | None = None
    city: str | None = None
    website: str | None = None
    year_established: int | None = None

    catchment_areas: list[CatchmentArea] = Field(default_factory=list)
    faculties: list[str] = Field(default_factory=list)
    programs: list[Program] = Field(default_factory=list)

    admission_requirements: AdmissionRequirements | None = None
    application_process: ApplicationProcess | None = None
    fee_tiers: list[FeeTier] = Field(default_factory=list)

    sources: list[Source] = Field(default_factory=list)
    raw_chunks: list[str] = Field(default_factory=list)
    confidence: dict[str, Any] = Field(default_factory=lambda: {"overall": "low", "missing_fields": []})
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    def compute_confidence(self) -> None:
        required = [
            "admission_requirements.utme_cutoff_general",
            "application_process.portal_url",
            "website",
            "faculties",
            "fee_tiers",
        ]
        missing: list[str] = []
        for path in required:
            if not _has_path(self, path):
                missing.append(path)

        filled = len(required) - len(missing)
        ratio = filled / len(required)
        if ratio >= 0.8:
            overall = "high"
        elif ratio >= 0.5:
            overall = "medium"
        else:
            overall = "low"

        self.confidence = {"overall": overall, "missing_fields": missing}


def _has_path(obj: BaseModel, path: str) -> bool:
    cur: Any = obj
    for part in path.split("."):
        if cur is None:
            return False
        if isinstance(cur, BaseModel):
            cur = getattr(cur, part, None)
        elif isinstance(cur, list):
            return len(cur) > 0
        else:
            cur = getattr(cur, part, None)
    if isinstance(cur, list):
        return len(cur) > 0
    return cur is not None


class ScrapeResult(BaseModel):
    scraped: int = 0
    failed: int = 0
    skipped: int = 0
    duration_sec: int = 0
    paths: dict[str, str] = Field(default_factory=dict)
    remaining_quota: dict[str, Any] | None = None
    paused: bool = False
    errors: list[str] = Field(default_factory=list)


class InstitutionSeed(BaseModel):
    """A seed entry for a Nigerian tertiary institution, before scraping."""

    name: str
    institution_type: InstitutionType
    type: OwnershipType
    state: str | None = None
    city: str | None = None
    website: str | None = None
    year_established: int | None = None
    short_name: str | None = None
    jamb_code: str | None = None
    contact_email: str | None = None
    phone: str | None = None
    address: str | None = None
    accreditation_body: str | None = None
    status: str | None = Field(default="active", description="active | inactive | suspended")
    admission_portal: str | None = None
