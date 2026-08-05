"""Tests for the validation module."""

from __future__ import annotations

import pytest

from naija_admissions.models import (
    AdmissionRequirements,
    CutoffEntry,
    FeeTier,
    Institution,
    InstitutionType,
    OwnershipType,
    Program,
)
from naija_admissions.validation import (
    has_blocking_errors,
    to_dict_list,
    validate_institution,
)


def _make_inst(**overrides):
    defaults = dict(
        institution_type=InstitutionType.UNIVERSITY,
        name="Test University",
        short_name="TU",
        type=OwnershipType.FEDERAL,
        state="Lagos",
        website="https://example.edu.ng",
        year_established=2000,
    )
    defaults.update(overrides)
    return Institution(**defaults)


def test_valid_institution_passes():
    inst = _make_inst()
    errors = validate_institution(inst)
    assert errors == []


def test_empty_name_fails():
    inst = _make_inst(name="")
    errors = validate_institution(inst)
    assert any(e.field == "name" and e.code == "name_empty" for e in errors)


def test_name_too_long_fails():
    inst = _make_inst(name="x" * 201)
    errors = validate_institution(inst)
    assert any(e.code == "name_too_long" for e in errors)


def test_utme_cutoff_out_of_range_fails():
    inst = _make_inst(admission_requirements=AdmissionRequirements(utme_cutoff_general=50))
    errors = validate_institution(inst)
    assert any(e.code == "utme_cutoff_out_of_range" for e in errors)


def test_utme_cutoff_in_range_passes():
    inst = _make_inst(admission_requirements=AdmissionRequirements(utme_cutoff_general=200))
    errors = validate_institution(inst)
    assert not any(e.code == "utme_cutoff_out_of_range" for e in errors)


def test_olevel_credits_out_of_range_fails():
    inst = _make_inst(admission_requirements=AdmissionRequirements(olevel_credits_min=3))
    errors = validate_institution(inst)
    assert any(e.code == "olevel_credits_out_of_range" for e in errors)


def test_duplicate_cutoff_warns():
    req = AdmissionRequirements(
        utme_cutoff_per_course=[
            CutoffEntry(course="Engineering", cutoff=200),
            CutoffEntry(course="Engineering", cutoff=200),
        ]
    )
    inst = _make_inst(admission_requirements=req)
    errors = validate_institution(inst)
    dup = [e for e in errors if e.code == "duplicate_cutoff"]
    assert len(dup) == 1
    assert dup[0].severity == "warning"


def test_conflicting_cutoff_warns():
    req = AdmissionRequirements(
        utme_cutoff_general=180,
        utme_cutoff_per_course=[CutoffEntry(course="Medicine", cutoff=300)],
    )
    inst = _make_inst(admission_requirements=req)
    errors = validate_institution(inst)
    assert any(e.code == "conflicting_cutoff" for e in errors)


def test_negative_fee_fails():
    inst = _make_inst(fee_tiers=[FeeTier(program_or_faculty="General", tuition_per_session_ngn=-100, source_url="https://example.edu.ng")])
    errors = validate_institution(inst)
    assert any(e.code == "fee_negative" for e in errors)


def test_excessive_fee_fails():
    inst = _make_inst(fee_tiers=[FeeTier(program_or_faculty="General", tuition_per_session_ngn=200_000_000, source_url="https://example.edu.ng")])
    errors = validate_institution(inst)
    assert any(e.code == "fee_excessive" for e in errors)


def test_invalid_website_url_fails():
    inst = _make_inst(website="not-a-url")
    errors = validate_institution(inst)
    assert any(e.code == "website_invalid" for e in errors)


def test_year_out_of_range_fails():
    inst = _make_inst(year_established=1500)
    errors = validate_institution(inst)
    assert any(e.code == "year_out_of_range" for e in errors)


def test_duplicate_program_warns():
    inst = _make_inst(programs=[
        Program(name="Computer Science"),
        Program(name="Computer Science"),
    ])
    errors = validate_institution(inst)
    assert any(e.code == "duplicate_program" for e in errors)


def test_has_blocking_errors():
    inst = _make_inst(name="")
    errors = validate_institution(inst)
    assert has_blocking_errors(errors)


def test_to_dict_list():
    inst = _make_inst(name="")
    errors = validate_institution(inst)
    dlist = to_dict_list(errors)
    assert all("field" in d and "code" in d and "message" in d for d in dlist)
