"""Tests for extraction models."""


import pytest

from naija_admissions.extraction_models import (
    CatchmentPolicy,
    ConfidenceLevel,
    CourseLevel,
    DegreeLevel,
    ExtractedAdmissionRequirements,
    ExtractedCatchment,
    ExtractedCourse,
    ExtractedDepartmentalCutoff,
    ExtractedFaculty,
    ExtractedFees,
    ExtractedInstitution,
    ExtractedKnowledge,
    FeeCategory,
    InstitutionType,
    OwnershipType,
    PostUTMEFormat,
)


class TestExtractionModels:
    """Test extraction Pydantic models."""

    def test_institution_model_valid(self):
        inst = ExtractedInstitution(
            name="University of Lagos",
            short_name="UNILAG",
            institution_type=InstitutionType.UNIVERSITY,
            ownership_type=OwnershipType.FEDERAL,
            state="Lagos",
            city="Lagos",
            website="https://unilag.edu.ng",
            admission_portal="https://admissions.unilag.edu.ng",
            year_established=1962,
            jamb_code="0405",
            confidence=ConfidenceLevel.HIGH,
            source_url="https://admissions.unilag.edu.ng",
        )
        assert inst.name == "University of Lagos"
        assert inst.institution_type == InstitutionType.UNIVERSITY
        assert inst.ownership_type == OwnershipType.FEDERAL
        assert inst.year_established == 1962

    def test_course_model_valid(self):
        course = ExtractedCourse(
            name="Computer Science",
            degree=DegreeLevel.BSC,
            level=CourseLevel.UNDERGRADUATE,
            duration_years=4,
            faculty_name="Faculty of Engineering",
            confidence=ConfidenceLevel.HIGH,
        )
        assert course.name == "Computer Science"
        assert course.degree == DegreeLevel.BSC
        assert course.duration_years == 4

    def test_course_duration_validation(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ExtractedCourse(
                name="Invalid Duration",
                duration_years=15,
            )

    def test_fees_model_required_amount(self):
        fee = ExtractedFees(
            fee_category=FeeCategory.TUITION,
            amount_ngn=126325,
            academic_session="2025/2026",
            confidence=ConfidenceLevel.MEDIUM,
        )
        assert fee.amount_ngn == 126325
        assert fee.fee_category == FeeCategory.TUITION

    def test_fees_validation_zero_amount_fails(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ExtractedFees(
                fee_category=FeeCategory.TUITION,
                amount_ngn=0,
                academic_session="2025/2026",
            )

    def test_admission_requirements_model(self):
        req = ExtractedAdmissionRequirements(
            olevel_credits_min=5,
            olevel_sittings_max=2,
            minimum_jamb=200,
            post_utme_required=True,
            post_utme_format=PostUTMEFormat.SCREENING,
            post_utme_weight_pct=30,
            aggregate_formula="(UTME/8) + (Post-UTME/2)",
            confidence=ConfidenceLevel.HIGH,
        )
        assert req.olevel_credits_min == 5
        assert req.minimum_jamb == 200
        assert req.post_utme_required is True

    def test_departmental_cutoff(self):
        cutoff = ExtractedDepartmentalCutoff(
            course_name="Computer Science",
            merit_cutoff=240.5,
            catchment_cutoff=230.0,
            elds_cutoff=220.0,
            academic_session="2025/2026",
            confidence=ConfidenceLevel.HIGH,
        )
        assert cutoff.merit_cutoff == 240.5
        assert cutoff.academic_session == "2025/2026"

    def test_catchment(self):
        catchment = ExtractedCatchment(
            name="ELDS States",
            eligible_states=["Adamawa", "Bauchi", "Bayelsa"],
            policy=CatchmentPolicy.ELDS,
            confidence=ConfidenceLevel.HIGH,
        )
        assert catchment.policy == CatchmentPolicy.ELDS
        assert len(catchment.eligible_states) == 3

    def test_complete_extracted_knowledge(self):
        extracted = ExtractedKnowledge(
            institution=ExtractedInstitution(
                name="Test Uni",
                institution_type=InstitutionType.UNIVERSITY,
                ownership_type=OwnershipType.FEDERAL,
                source_url="https://test.edu.ng",
                confidence=ConfidenceLevel.HIGH,
            ),
            faculties=[
                ExtractedFaculty(name="Faculty of Science", confidence=ConfidenceLevel.HIGH),
                ExtractedFaculty(name="Faculty of Arts", confidence=ConfidenceLevel.HIGH),
            ],
            courses=[
                ExtractedCourse(
                    name="Computer Science",
                    degree=DegreeLevel.BSC,
                    level=CourseLevel.UNDERGRADUATE,
                    duration_years=4,
                    confidence=ConfidenceLevel.HIGH,
                ),
            ],
            admission_requirements=[
                ExtractedAdmissionRequirements(
                    minimum_jamb=200,
                    confidence=ConfidenceLevel.HIGH,
                ),
            ],
            departmental_cutoffs=[
                ExtractedDepartmentalCutoff(
                    course_name="Computer Science",
                    merit_cutoff=240.0,
                    academic_session="2025/2026",
                    confidence=ConfidenceLevel.HIGH,
                ),
            ],
            fees=[
                ExtractedFees(
                    fee_category=FeeCategory.TUITION,
                    amount_ngn=100000,
                    academic_session="2025/2026",
                    confidence=ConfidenceLevel.MEDIUM,
                ),
            ],
            extraction_confidence=ConfidenceLevel.HIGH,
        )
        assert extracted.institution.name == "Test Uni"
        assert len(extracted.faculties) == 2
        assert len(extracted.courses) == 1
        assert extracted.extraction_confidence == ConfidenceLevel.HIGH

    def test_institution_default_confidence_is_low(self):
        inst = ExtractedInstitution(
            name="Test",
            institution_type=InstitutionType.UNIVERSITY,
            ownership_type=OwnershipType.FEDERAL,
            source_url="https://test.edu.ng",
        )
        assert inst.confidence == ConfidenceLevel.LOW

    def test_knowledge_default_lists_empty(self):
        knowledge = ExtractedKnowledge(
            institution=ExtractedInstitution(
                name="Test",
                institution_type=InstitutionType.UNIVERSITY,
                ownership_type=OwnershipType.FEDERAL,
                source_url="https://test.edu.ng",
            ),
        )
        assert knowledge.faculties == []
        assert knowledge.courses == []
        assert knowledge.admission_requirements == []
        assert knowledge.fees == []


class TestSerDe:
    """Test serialization and deserialization."""

    def test_json_round_trip_full(self):
        original = ExtractedKnowledge(
            institution=ExtractedInstitution(
                name="Test Uni",
                institution_type=InstitutionType.UNIVERSITY,
                ownership_type=OwnershipType.FEDERAL,
                source_url="https://test.edu.ng",
                confidence=ConfidenceLevel.HIGH,
            ),
            faculties=[
                ExtractedFaculty(name="Faculty A", confidence=ConfidenceLevel.HIGH),
            ],
            courses=[
                ExtractedCourse(
                    name="CS",
                    degree=DegreeLevel.BSC,
                    duration_years=4,
                    confidence=ConfidenceLevel.HIGH,
                ),
            ],
            fees=[
                ExtractedFees(
                    fee_category=FeeCategory.TUITION,
                    amount_ngn=50000,
                    academic_session="2025/2026",
                    confidence=ConfidenceLevel.MEDIUM,
                ),
            ],
        )

        json_str = original.model_dump_json()
        restored = ExtractedKnowledge.model_validate_json(json_str)
        assert restored.institution.name == original.institution.name
        assert len(restored.faculties) == len(original.faculties)
        assert len(restored.courses) == len(original.courses)
        assert restored.fees[0].amount_ngn == original.fees[0].amount_ngn

    def test_invalid_json_raises(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ExtractedKnowledge.model_validate_json('{"invalid": "data"}')

    def test_validation_helper_accepts_dict(self):
        from naija_admissions.extraction_models import validate_extracted_knowledge

        data = {
            "institution": {
                "name": "Dict Uni",
                "institution_type": "university",
                "ownership_type": "federal",
                "source_url": "https://dict.edu.ng",
            },
            "faculties": [],
            "courses": [],
        }
        result = validate_extracted_knowledge(data)
        assert result.institution.name == "Dict Uni"

    def test_confidence_calculation(self):
        from naija_admissions.extraction_models import calculate_overall_confidence

        knowledge = ExtractedKnowledge(
            institution=ExtractedInstitution(
                name="Test",
                institution_type=InstitutionType.UNIVERSITY,
                ownership_type=OwnershipType.FEDERAL,
                source_url="https://test.edu.ng",
                confidence=ConfidenceLevel.HIGH,
            ),
            faculties=[
                ExtractedFaculty(name="A", confidence=ConfidenceLevel.HIGH),
                ExtractedFaculty(name="B", confidence=ConfidenceLevel.HIGH),
            ],
            courses=[
                ExtractedCourse(name="C", confidence=ConfidenceLevel.HIGH),
            ],
        )
        confidence = calculate_overall_confidence(knowledge)
        assert confidence == ConfidenceLevel.HIGH
