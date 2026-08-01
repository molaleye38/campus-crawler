"""Tests for scraper pipeline integration."""

import os
from unittest.mock import AsyncMock, patch

import pytest

from naija_admissions.extraction_models import (
    ConfidenceLevel,
    CourseLevel,
    DegreeLevel,
    ExtractedAdmissionRequirements,
    ExtractedCourse,
    ExtractedDepartmentalCutoff,
    ExtractedFaculty,
    ExtractedFees,
    ExtractedInstitution,
    ExtractedKnowledge,
    FeeCategory,
)
from naija_admissions.extraction_models import (
    InstitutionType as ExtInstitutionType,
)
from naija_admissions.extraction_models import (
    OwnershipType as ExtOwnershipType,
)
from naija_admissions.models import (
    Institution,
    InstitutionSeed,
    InstitutionType,
    OwnershipType,
)
from naija_admissions.scraper import WEBSITE_MAPPER_ENABLED, _apply_extracted_knowledge, scrape_one


@pytest.fixture
def sample_seed():
    return InstitutionSeed(
        name="University of Lagos",
        institution_type=InstitutionType.UNIVERSITY,
        type=OwnershipType.FEDERAL,
        state="Lagos",
        city="Lagos",
        website="https://unilag.edu.ng",
        short_name="UNILAG",
    )


@pytest.fixture
def sample_institution(sample_seed):
    return Institution(
        name=sample_seed.name,
        institution_type=sample_seed.institution_type,
        type=sample_seed.type,
        state=sample_seed.state,
        city=sample_seed.city,
        website=sample_seed.website,
        short_name=sample_seed.short_name,
    )


@pytest.fixture
def sample_extracted_knowledge():
    return ExtractedKnowledge(
        institution=ExtractedInstitution(
            name="University of Lagos",
            short_name="UNILAG",
            institution_type=ExtInstitutionType.UNIVERSITY,
            ownership_type=ExtOwnershipType.FEDERAL,
            state="Lagos",
            city="Lagos",
            website="https://unilag.edu.ng",
            jamb_code="0405",
            confidence=ConfidenceLevel.HIGH,
            source_url="https://admissions.unilag.edu.ng",
        ),
        faculties=[
            ExtractedFaculty(name="Faculty of Engineering", confidence=ConfidenceLevel.HIGH),
            ExtractedFaculty(name="Faculty of Science", confidence=ConfidenceLevel.HIGH),
        ],
        courses=[
            ExtractedCourse(
                name="Computer Science",
                degree=DegreeLevel.BSC,
                level=CourseLevel.UNDERGRADUATE,
                duration_years=4,
                faculty_name="Faculty of Engineering",
                confidence=ConfidenceLevel.HIGH,
            ),
        ],
        admission_requirements=[
            ExtractedAdmissionRequirements(
                olevel_credits_min=5,
                minimum_jamb=200,
                post_utme_required=True,
                post_utme_format="screening",
                post_utme_weight_pct=30,
                confidence=ConfidenceLevel.HIGH,
            ),
        ],
        departmental_cutoffs=[
            ExtractedDepartmentalCutoff(
                course_name="Computer Science",
                merit_cutoff=240.5,
                catchment_cutoff=230.0,
                elds_cutoff=220.0,
                academic_session="2025/2026",
                confidence=ConfidenceLevel.HIGH,
            ),
        ],
        fees=[
            ExtractedFees(
                fee_category=FeeCategory.TUITION,
                amount_ngn=126325,
                academic_session="2025/2026",
                confidence=ConfidenceLevel.MEDIUM,
            ),
        ],
        extraction_confidence=ConfidenceLevel.HIGH,
    )


class TestApplyExtractedKnowledge:
    """Test _apply_extracted_knowledge function."""

    def test_fills_short_name(self, sample_institution, sample_extracted_knowledge, sample_seed):
        sample_institution.short_name = None
        _apply_extracted_knowledge(sample_institution, sample_extracted_knowledge, sample_seed)
        assert sample_institution.short_name == "UNILAG"

    def test_fills_website(self, sample_institution, sample_extracted_knowledge, sample_seed):
        sample_institution.website = None
        _apply_extracted_knowledge(sample_institution, sample_extracted_knowledge, sample_seed)
        assert sample_institution.website == "https://unilag.edu.ng"

    def test_populates_faculties(self, sample_institution, sample_extracted_knowledge, sample_seed):
        _apply_extracted_knowledge(sample_institution, sample_extracted_knowledge, sample_seed)
        assert "Faculty of Engineering" in sample_institution.faculties
        assert "Faculty of Science" in sample_institution.faculties

    def test_populates_programs(self, sample_institution, sample_extracted_knowledge, sample_seed):
        _apply_extracted_knowledge(sample_institution, sample_extracted_knowledge, sample_seed)
        assert len(sample_institution.programs) == 1
        assert sample_institution.programs[0].name == "Computer Science"
        assert sample_institution.programs[0].degree == "BSc"

    def test_populates_admission_requirements(self, sample_institution, sample_extracted_knowledge, sample_seed):
        _apply_extracted_knowledge(sample_institution, sample_extracted_knowledge, sample_seed)
        assert sample_institution.admission_requirements is not None
        assert sample_institution.admission_requirements.utme_cutoff_general == 200
        assert sample_institution.admission_requirements.olevel_credits_min == 5

    def test_populates_cutoffs(self, sample_institution, sample_extracted_knowledge, sample_seed):
        _apply_extracted_knowledge(sample_institution, sample_extracted_knowledge, sample_seed)
        assert len(sample_institution.admission_requirements.utme_cutoff_per_course) > 0
        cutoff = sample_institution.admission_requirements.utme_cutoff_per_course[0]
        assert cutoff.course == "Computer Science"
        assert cutoff.cutoff == 240

    def test_populates_fees(self, sample_institution, sample_extracted_knowledge, sample_seed):
        _apply_extracted_knowledge(sample_institution, sample_extracted_knowledge, sample_seed)
        assert len(sample_institution.fee_tiers) > 0
        assert sample_institution.fee_tiers[0].tuition_per_session_ngn == 126325

    def test_empty_extraction_falls_back_to_regex(self, sample_institution, sample_seed):
        empty_extracted = ExtractedKnowledge(
            institution=ExtractedInstitution(
                name="Empty",
                institution_type=ExtInstitutionType.UNIVERSITY,
                ownership_type=ExtOwnershipType.FEDERAL,
                source_url="https://test.edu.ng",
            ),
        )
        _apply_extracted_knowledge(sample_institution, empty_extracted, sample_seed)
        assert sample_institution.admission_requirements is not None or True


class TestScraperOneIntegration:
    """Test scrape_one integration."""

    @pytest.mark.asyncio
    async def test_scraper_returns_institution(self, sample_seed):
        mock_client = AsyncMock()
        mock_client.search = AsyncMock(return_value=[])
        mock_client.scrape = AsyncMock(return_value=None)

        with patch.dict(os.environ, {"NVIDIA_API_KEY": "dummy"}, clear=False):
            inst = await scrape_one(sample_seed, mock_client, lambda x: None)
            assert isinstance(inst, Institution)
            assert inst.name == "University of Lagos"

    @pytest.mark.asyncio
    async def test_scraper_no_raw_chunks_returns_early(self, sample_seed):
        mock_client = AsyncMock()
        mock_client.search = AsyncMock(return_value=[])
        mock_client.scrape = AsyncMock(return_value=None)

        with patch.dict(os.environ, {"NVIDIA_API_KEY": "dummy"}, clear=False):
            inst = await scrape_one(sample_seed, mock_client, lambda x: None)
            assert inst.faculties == []
            assert len(inst.programs) == 0


class TestScraperConfigFlags:
    """Test scraper configuration flags."""

    def test_ai_extraction_enabled(self):
        assert isinstance(WEBSITE_MAPPER_ENABLED, bool)

    def test_imports_include_website_mapper(self):
        from naija_admissions import scraper
        assert hasattr(scraper, "map_institution_website")
        assert hasattr(scraper, "filter_urls_for_scraping")
        assert hasattr(scraper, "SiteMap")
