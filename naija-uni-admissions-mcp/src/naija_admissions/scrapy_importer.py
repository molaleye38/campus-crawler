"""Scrapy data importer — reads Scrapy JSONLines output and enriches the pipeline.

This module reads files produced by Scrapy spiders (in data/scrapy_data/)
and provides typed accessors + enrichment functions for the existing pipeline.

No Scrapy dependency — pure JSONLines reading with pydantic validation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import InstitutionSeed, InstitutionType, OwnershipType

SCRAPY_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "scrapy_data"
JAMB_PROGRAMS_PATH = SCRAPY_DATA_DIR / "jamb_programs.jsonl"
JAMB_SEEDS_PATH = SCRAPY_DATA_DIR / "jamb_seeds.jsonl"
NUC_PROGRAMS_PATH = SCRAPY_DATA_DIR / "nuc_programs.jsonl"
PORTAL_ADMISSIONS_PATH = SCRAPY_DATA_DIR / "portal_admissions.jsonl"


# ── Typed data structures ────────────────────────────────────────────────

class JambProgramme:
    """Single JAMB programme record from JSONLines."""
    def __init__(self, data: dict[str, Any]) -> None:
        self.institution: str = data.get("institution", "").strip()
        self.programme: str = data.get("programme", "").strip()
        self.utme_subjects_raw: str = data.get("utme_subjects_raw", "").strip()
        self.olevel_requirements_raw: str = data.get("olevel_requirements_raw", "").strip()
        self.cutoff: int | None = data.get("cutoff")
        self.source_url: str = data.get("source_url", "").strip()

    @property
    def utme_subjects(self) -> list[str]:
        if not self.utme_subjects_raw:
            return []
        # Split on common delimiters
        import re
        return [s.strip() for s in re.split(r"[,/;|]", self.utme_subjects_raw) if s.strip()]

    @property
    def olevel_subjects(self) -> list[str]:
        if not self.olevel_requirements_raw:
            return []
        import re
        return [s.strip() for s in re.split(r"[,/;|]", self.olevel_requirements_raw) if s.strip()]


class NucAccreditation:
    """Single NUC accreditation record."""
    def __init__(self, data: dict[str, Any]) -> None:
        self.institution: str = data.get("institution", "").strip()
        self.ownership: str = data.get("ownership", "").strip().lower()
        self.programme: str = data.get("programme", "").strip()
        self.accreditation_status: str = data.get("accreditation_status", "").strip()
        self.accreditation_expiry: str = data.get("accreditation_expiry", "").strip()
        self.source_url: str = data.get("source_url", "").strip()


class PortalAdmissionPage:
    """Single portal admission page record."""
    def __init__(self, data: dict[str, Any]) -> None:
        self.url: str = data.get("url", "").strip()
        self.title: str = data.get("title", "").strip()
        self.main_text: str = data.get("main_text", "").strip()
        self.tables: list[dict[str, Any]] = data.get("tables", [])
        self.lists: list[list[str]] = data.get("lists", [])
        self.depth: int = data.get("depth", 0)


# ── Loaders ──────────────────────────────────────────────────────────────

def _load_jsonl(path: Path, cls) -> list:
    """Load JSONLines file into typed objects."""
    if not path.exists():
        return []
    items = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                items.append(cls(data))
            except json.JSONDecodeError:
                continue
    return items


def load_jamb_programmes() -> list[JambProgramme]:
    """Load JAMB programme data from scrapy output."""
    return _load_jsonl(JAMB_PROGRAMS_PATH, JambProgramme)


def load_jamb_seeds() -> list[dict[str, Any]]:
    """Load JAMB institution seeds from scrapy output (dicts for flexibility)."""
    if not JAMB_SEEDS_PATH.exists():
        return []
    items = []
    with JAMB_SEEDS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return items


def load_nuc_accreditations() -> list[NucAccreditation]:
    """Load NUC accreditation data from scrapy output."""
    return _load_jsonl(NUC_PROGRAMS_PATH, NucAccreditation)


def load_portal_admissions() -> list[PortalAdmissionPage]:
    """Load portal admission pages from scrapy output."""
    return _load_jsonl(PORTAL_ADMISSIONS_PATH, PortalAdmissionPage)


# ── Enrichment functions ────────────────────────────────────────────────

def _normalize_name(name: str) -> str:
    """Normalize institution name for matching."""
    return name.lower().strip().replace("university of ", "").replace("federal ", "").replace("state ", "")


def enrich_institutions(seeds: list[InstitutionSeed]) -> list[InstitutionSeed]:
    """Merge JAMB-discovered seeds into the existing seed list.

    Returns a NEW list (does not mutate input). Adds new institutions
    found by JAMB spider and updates website/state for matches.
    """
    jamb_seeds = load_jamb_seeds()
    if not jamb_seeds:
        return list(seeds)  # no enrichment data, return copy

    # Build lookup from existing seeds - create copies to avoid mutation
    enriched = []
    existing_by_norm = {}
    existing_names = set()
    for s in seeds:
        copy = InstitutionSeed(
            name=s.name,
            institution_type=s.institution_type,
            type=s.type,
            state=s.state,
            website=s.website,
            year_established=s.year_established,
            city=s.city,
            short_name=s.short_name,
            jamb_code=s.jamb_code,
            contact_email=s.contact_email,
            phone=s.phone,
            address=s.address,
            accreditation_body=s.accreditation_body,
            status=s.status,
            admission_portal=s.admission_portal,
        )
        enriched.append(copy)
        existing_by_norm[_normalize_name(s.name)] = copy
        existing_names.add(s.name)

    for jseed in jamb_seeds:
        jname = jseed.get("name", "").strip()
        if not jname:
            continue

        norm = _normalize_name(jname)
        if norm in existing_by_norm:
            # Update existing seed copy with better data from JAMB
            existing = existing_by_norm[norm]
            if jseed.get("website") and not existing.website:
                existing.website = jseed["website"]
            if jseed.get("state") and not existing.state:
                existing.state = jseed["state"]
        elif jname not in existing_names:
            # New institution discovered by JAMB
            new_seed = InstitutionSeed(
                name=jname,
                institution_type=InstitutionType.UNIVERSITY,  # default
                type=OwnershipType.FEDERAL,  # default
                state=jseed.get("state"),
                website=jseed.get("website"),
                year_established=None,
            )
            enriched.append(new_seed)
            existing_names.add(jname)

    return enriched


def enrich_programmes(
    institution_name: str,
    scrapy_programmes: list[JambProgramme] | None = None,
) -> list[JambProgramme]:
    """Return JAMB programmes for a specific institution."""
    if scrapy_programmes is None:
        scrapy_programmes = load_jamb_programmes()
    norm_target = _normalize_name(institution_name)
    return [p for p in scrapy_programmes if _normalize_name(p.institution) == norm_target]


def get_nuc_status(institution_name: str, programme: str) -> NucAccreditation | None:
    """Check NUC accreditation status for a programme."""
    nuc_records = load_nuc_accreditations()
    norm_inst = _normalize_name(institution_name)
    norm_prog = programme.lower().strip()
    for rec in nuc_records:
        if _normalize_name(rec.institution) == norm_inst and rec.programme.lower().strip() == norm_prog:
            return rec
    return None


def get_portal_pages_for_domain(domain: str) -> list[PortalAdmissionPage]:
    """Filter portal pages by domain."""
    pages = load_portal_admissions()
    domain = domain.lower()
    return [p for p in pages if domain in p.url.lower()]