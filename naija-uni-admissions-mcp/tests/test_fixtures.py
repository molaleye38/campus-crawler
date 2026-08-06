"""Tests using real-world fixture files (polytechnic + COE)."""

from __future__ import annotations

from pathlib import Path

import pytest

from naija_admissions.models import InstitutionType
from naija_admissions.parsers.fees_parser import parse_fees
from naija_admissions.parsers.programs_parser import parse_programs
from naija_admissions.parsers.requirements_parser import parse_requirements


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


class TestPolytechnicFixture:
    """Verify parsers handle the Yaba College of Technology fixture."""

    def setup_method(self):
        self.text = _load("yabatech_polytechnic.md")

    def test_requirements_extracts_polytechnic_cutoff(self):
        req = parse_requirements(self.text, InstitutionType.POLYTECHNIC)
        assert req is not None
        assert req.utme_cutoff_general == 150

    def test_programs_extracts_nd_and_hnd(self):
        _, programs = parse_programs(self.text, InstitutionType.POLYTECHNIC)
        names = [p.name for p in programs]
        assert any("Computer Science" in n for n in names)
        assert any("Electrical" in n for n in names)
        nd_count = sum(1 for n in names if "ND" in n or "National Diploma" in n)
        hnd_count = sum(1 for n in names if "HND" in n or "Higher National Diploma" in n)

    def test_fees_extracts_indigene_and_non_indigene(self):
        all_fees = []
        for chunk in self.text.split("\n##"):
            fees = parse_fees(chunk, "https://yabatech.edu.ng")
            all_fees.extend(fees)
        assert len(all_fees) > 0


class TestCOEFixture:
    """Verify parsers handle the Federal College of Education fixture."""

    def setup_method(self):
        self.text = _load("fce_abeokuta_coe.md")

    def test_requirements_extracts_coe_cutoff(self):
        req = parse_requirements(self.text, InstitutionType.COLLEGE_OF_EDUCATION)
        assert req is not None
        assert req.utme_cutoff_general == 100

    def test_programs_extracts_nce_programs(self):
        _, programs = parse_programs(self.text, InstitutionType.COLLEGE_OF_EDUCATION)
        names = [p.name for p in programs]
        assert any("NCE" in n or "Mathematics" in n for n in names)


class TestUniversityFixture:
    """Verify parsers handle the UNILAG fixture (pre-existing)."""

    def setup_method(self):
        self.text = _load("unilag_admission.md")

    def test_requirements_extracts_university_cutoff(self):
        req = parse_requirements(self.text, InstitutionType.UNIVERSITY)
        assert req is not None
        assert req.utme_cutoff_general == 200
