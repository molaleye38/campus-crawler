"""Tests for scrapy_importer module."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from naija_admissions.scrapy_importer import (
    JambProgramme,
    NucAccreditation,
    PortalAdmissionPage,
    load_jamb_programmes,
    load_jamb_seeds,
    load_nuc_accreditations,
    load_portal_admissions,
    enrich_institutions,
    enrich_programmes,
    get_nuc_status,
    get_portal_pages_for_domain,
    SCRAPY_DATA_DIR,
    JAMB_PROGRAMS_PATH,
    JAMB_SEEDS_PATH,
    NUC_PROGRAMS_PATH,
    PORTAL_ADMISSIONS_PATH,
)
from naija_admissions.models import InstitutionSeed, InstitutionType, OwnershipType


@pytest.fixture
def mock_scrapy_data(monkeypatch):
    """Create mock scrapy JSONLines files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # Mock paths
        jamb_programs = tmp / "jamb_programs.jsonl"
        jamb_seeds = tmp / "jamb_seeds.jsonl"
        nuc_programs = tmp / "nuc_programs.jsonl"
        portal_pages = tmp / "portal_admissions.jsonl"

        # Write JAMB programmes
        jamb_data = [
            {"institution": "University of Lagos", "programme": "Computer Science",
             "utme_subjects_raw": "English, Mathematics, Physics, Chemistry",
             "olevel_requirements_raw": "English, Mathematics, Physics, Chemistry, Biology",
             "cutoff": 200, "source_url": "https://jamb.gov.ng/ibass/unilag"},
            {"institution": "University of Lagos", "programme": "Medicine and Surgery",
             "utme_subjects_raw": "English, Biology, Chemistry, Physics",
             "olevel_requirements_raw": "English, Mathematics, Biology, Chemistry, Physics",
             "cutoff": 250, "source_url": "https://jamb.gov.ng/ibass/unilag"},
            {"institution": "Ahmadu Bello University", "programme": "Computer Science",
             "utme_subjects_raw": "English, Mathematics, Physics",
             "olevel_requirements_raw": "English, Mathematics, Physics, Chemistry",
             "cutoff": 180, "source_url": "https://jamb.gov.ng/ibass/abu"},
        ]
        with jamb_programs.open("w", encoding="utf-8") as f:
            for item in jamb_data:
                f.write(json.dumps(item) + "\n")

        # Write JAMB seeds
        seed_data = [
            {"name": "New Federal University", "type": "federal", "state": "Kano",
             "website": "https://newfed.edu.ng", "jamb_code": "NEWFE"},
            {"name": "University of Lagos", "type": "federal", "state": "Lagos",
             "website": "https://www.unilag.edu.ng", "jamb_code": "UNILAG"},
        ]
        with jamb_seeds.open("w", encoding="utf-8") as f:
            for item in seed_data:
                f.write(json.dumps(item) + "\n")

        # Write NUC programmes
        nuc_data = [
            {"institution": "University of Lagos", "ownership": "federal",
             "programme": "Computer Science", "accreditation_status": "Full",
             "accreditation_expiry": "2029", "source_url": "https://nuc.edu.ng/unilag"},
            {"institution": "Ahmadu Bello University", "ownership": "federal",
             "programme": "Computer Science", "accreditation_status": "Interim",
             "accreditation_expiry": "2027", "source_url": "https://nuc.edu.ng/abu"},
        ]
        with nuc_programs.open("w", encoding="utf-8") as f:
            for item in nuc_data:
                f.write(json.dumps(item) + "\n")

        # Write portal pages
        portal_data = [
            {"url": "https://www.unilag.edu.ng/admissions", "title": "UNILAG Admissions",
             "main_text": "Admission requirements and fees information",
             "tables": [{"headers": ["Programme", "Fee"], "rows": [["CS", "100000"]]}],
             "lists": [["Apply online", "Pay fee", "Submit docs"]],
             "depth": 1},
            {"url": "https://www.abu.edu.ng/apply", "title": "ABU Apply",
             "main_text": "Application portal for ABU",
             "tables": [], "lists": [["Step 1", "Step 2"]], "depth": 0},
        ]
        with portal_pages.open("w", encoding="utf-8") as f:
            for item in portal_data:
                f.write(json.dumps(item) + "\n")

        # Patch module paths
        monkeypatch.setattr("naija_admissions.scrapy_importer.SCRAPY_DATA_DIR", tmp)
        monkeypatch.setattr("naija_admissions.scrapy_importer.JAMB_PROGRAMS_PATH", jamb_programs)
        monkeypatch.setattr("naija_admissions.scrapy_importer.JAMB_SEEDS_PATH", jamb_seeds)
        monkeypatch.setattr("naija_admissions.scrapy_importer.NUC_PROGRAMS_PATH", nuc_programs)
        monkeypatch.setattr("naija_admissions.scrapy_importer.PORTAL_ADMISSIONS_PATH", portal_pages)

        yield


def test_load_jamb_programmes(mock_scrapy_data):
    programmes = load_jamb_programmes()
    assert len(programmes) == 3
    assert isinstance(programmes[0], JambProgramme)
    assert programmes[0].institution == "University of Lagos"
    assert programmes[0].programme == "Computer Science"
    assert programmes[0].cutoff == 200
    assert "English" in programmes[0].utme_subjects
    assert "Physics" in programmes[0].utme_subjects


def test_load_jamb_seeds(mock_scrapy_data):
    seeds = load_jamb_seeds()
    assert len(seeds) == 2
    assert seeds[0]["name"] == "New Federal University"
    assert seeds[0]["jamb_code"] == "NEWFE"


def test_load_nuc_accreditations(mock_scrapy_data):
    nuc = load_nuc_accreditations()
    assert len(nuc) == 2
    assert isinstance(nuc[0], NucAccreditation)
    assert nuc[0].institution == "University of Lagos"
    assert nuc[0].accreditation_status == "Full"


def test_load_portal_admissions(mock_scrapy_data):
    pages = load_portal_admissions()
    assert len(pages) == 2
    assert isinstance(pages[0], PortalAdmissionPage)
    assert pages[0].url == "https://www.unilag.edu.ng/admissions"
    assert len(pages[0].tables) == 1
    assert pages[0].tables[0]["headers"] == ["Programme", "Fee"]


def test_enrich_institutions_adds_new(mock_scrapy_data):
    existing = [
        InstitutionSeed(
            name="University of Lagos",
            institution_type=InstitutionType.UNIVERSITY,
            type=OwnershipType.FEDERAL,
            state="Lagos",
            website=None,
        ),
    ]
    enriched = enrich_institutions(existing)
    # Should add the new federal university
    names = [s.name for s in enriched]
    assert "New Federal University" in names
    # Should have updated UNILAG website
    unilag = next(s for s in enriched if s.name == "University of Lagos")
    assert unilag.website == "https://www.unilag.edu.ng"


def test_enrich_institutions_no_mutation(mock_scrapy_data):
    original = [
        InstitutionSeed(
            name="University of Lagos",
            institution_type=InstitutionType.UNIVERSITY,
            type=OwnershipType.FEDERAL,
            state="Lagos",
            website=None,
        ),
    ]
    original_website = original[0].website
    enrich_institutions(original)
    # Original list should not be mutated
    assert original[0].website is original_website


def test_enrich_programmes_filters_by_institution(mock_scrapy_data):
    all_progs = load_jamb_programmes()
    unilag_progs = enrich_programmes("University of Lagos", all_progs)
    assert len(unilag_progs) == 2
    assert all(p.institution == "University of Lagos" for p in unilag_progs)


def test_get_nuc_status_found(mock_scrapy_data):
    status = get_nuc_status("University of Lagos", "Computer Science")
    assert status is not None
    assert status.accreditation_status == "Full"


def test_get_nuc_status_not_found(mock_scrapy_data):
    status = get_nuc_status("University of Lagos", "Non-existent Programme")
    assert status is None


def test_get_portal_pages_for_domain(mock_scrapy_data):
    pages = get_portal_pages_for_domain("unilag.edu.ng")
    assert len(pages) == 1
    assert "unilag.edu.ng" in pages[0].url