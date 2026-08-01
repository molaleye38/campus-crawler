"""Tests for parsers."""


from naija_admissions.models import (
    InstitutionType,
    OwnershipType,
)
from naija_admissions.parsers.catchment_parser import parse_catchment
from naija_admissions.parsers.fees_parser import parse_fees
from naija_admissions.parsers.programs_parser import parse_programs
from naija_admissions.parsers.requirements_parser import parse_requirements


class TestRequirementsParser:
    """Test requirements_parser."""

    def test_basic_utme_cutoff(self):
        text = "The UTME cut-off mark is 200."
        req = parse_requirements(text, InstitutionType.UNIVERSITY)
        assert req is not None
        assert req.utme_cutoff_general == 200

    def test_high_cutoff(self):
        text = "The minimum UTME score is 280."
        req = parse_requirements(text, InstitutionType.UNIVERSITY)
        assert req is not None
        assert req.utme_cutoff_general == 280

    def test_polytechnic_cutoff_lower(self):
        text = "The minimum UTME score is 120."
        req = parse_requirements(text, InstitutionType.POLYTECHNIC)
        assert req is not None
        assert req.utme_cutoff_general == 120


class TestFeesParser:
    """Test fees_parser."""

    def test_basic_tuition(self):
        text = "Tuition fee: NGN 100,000 per session."
        fees = parse_fees(text, "https://test.edu.ng")
        assert len(fees) >= 1
        assert any(f.tuition_per_session_ngn == 100000 for f in fees)

    def test_multiple_fees(self):
        text = """
        Tuition fee: NGN 50,000
        Application fee: NGN 2,000
        Acceptance fee: NGN 20,000
        Hostel: NGN 15,000
        """
        fees = parse_fees(text, "https://test.edu.ng")
        assert len(fees) >= 1


class TestProgramsParser:
    """Test programs_parser."""

    def test_programs_extraction(self):
        text = """
        The university offers:
        - Computer Science (B.Sc)
        - Medicine and Surgery (MBBS)
        - Law (LL.B)
        - Electrical Engineering (B.Eng)
        """
        faculties, programs = parse_programs(text, InstitutionType.UNIVERSITY)
        assert len(programs) >= 3
        names = [p.name for p in programs]
        assert any("Computer Science" in n for n in names)

    def test_polytechnic_programs(self):
        text = """
        Programmes:
        - Accountancy (ND)
        - Business Administration (HND)
        """
        faculties, programs = parse_programs(text, InstitutionType.POLYTECHNIC)
        assert len(programs) >= 1


class TestCatchmentParser:
    """Test catchment_parser."""

    def test_no_catchment_for_polytechnic(self):
        text = "Catchment areas: Lagos, Ogun, Oyo states."
        catchment = parse_catchment(
            text,
            InstitutionType.POLYTECHNIC,
            OwnershipType.FEDERAL.value,
            "Lagos",
        )
        assert isinstance(catchment, list)
        # Polytechnics typically return empty or a "none" placeholder
        if catchment:
            assert all(c.policy is not None for c in catchment)

    def test_university_catchment(self):
        text = "The university's catchment includes ELDS states and Lagos indigenes."
        catchment = parse_catchment(
            text,
            InstitutionType.UNIVERSITY,
            OwnershipType.FEDERAL.value,
            "Lagos",
        )
        assert isinstance(catchment, list)
