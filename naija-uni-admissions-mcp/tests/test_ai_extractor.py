"""Tests for ai_extractor."""

import os
from unittest.mock import AsyncMock, patch

import pytest

from naija_admissions.ai_extractor import NVIDIAExtractor, extract_with_nvidia
from naija_admissions.extraction_models import (
    ConfidenceLevel,
    ExtractedInstitution,
    ExtractedKnowledge,
    InstitutionType,
    OwnershipType,
)


class TestNVIDIAExtractorInit:
    """Test NVIDIAExtractor initialization."""

    def test_init_with_api_key(self):
        ex = NVIDIAExtractor(api_key="test-key")
        assert ex.api_key == "test-key"
        assert ex.model is not None

    def test_init_without_api_key_raises(self):
        import os
        old_key = os.environ.pop("NVIDIA_API_KEY", None)
        try:
            with pytest.raises(RuntimeError):
                NVIDIAExtractor()
        finally:
            if old_key:
                os.environ["NVIDIA_API_KEY"] = old_key

    def test_init_with_env_var(self):
        import os
        os.environ["NVIDIA_API_KEY"] = "env-key"
        try:
            ex = NVIDIAExtractor()
            assert ex.api_key == "env-key"
        finally:
            del os.environ["NVIDIA_API_KEY"]

    def test_custom_model_override(self):
        ex = NVIDIAExtractor(api_key="test", model="custom-model")
        assert ex.model == "custom-model"

    def test_base_url_strips_trailing_slash(self):
        ex = NVIDIAExtractor(api_key="test", base_url="https://api.example.com/v1/")
        assert ex.base_url == "https://api.example.com/v1"


class TestFallbackExtraction:
    """Test fallback extraction when API fails."""

    def test_fallback_returns_valid_knowledge(self):
        ex = NVIDIAExtractor(api_key="dummy")
        result = ex._fallback_extraction(
            source_url="https://test.edu.ng",
            institution_type="university",
        )
        assert isinstance(result, ExtractedKnowledge)
        assert result.institution.name == "Unknown Institution"
        assert result.institution.source_url == "https://test.edu.ng"
        assert result.institution.institution_type == InstitutionType.UNIVERSITY
        assert result.extraction_confidence == ConfidenceLevel.LOW

    def test_fallback_with_polytechnic(self):
        ex = NVIDIAExtractor(api_key="dummy")
        result = ex._fallback_extraction(
            source_url="https://test.edu.ng",
            institution_type="polytechnic",
        )
        assert result.institution.institution_type == InstitutionType.POLYTECHNIC

    def test_fallback_with_invalid_type_raises(self):
        from pydantic import ValidationError
        ex = NVIDIAExtractor(api_key="dummy")
        with pytest.raises((ValueError, ValidationError)):
            ex._fallback_extraction(
                source_url="https://test.edu.ng",
                institution_type="invalid_type",
            )


class TestExtractWithNVIDIA:
    """Test extract_with_nvidia convenience function."""

    @pytest.mark.asyncio
    async def test_extract_returns_knowledge(self):
        mock_knowledge = ExtractedKnowledge(
            institution=ExtractedInstitution(
                name="Mock University",
                institution_type=InstitutionType.UNIVERSITY,
                ownership_type=OwnershipType.FEDERAL,
                source_url="https://mock.edu.ng",
                confidence=ConfidenceLevel.HIGH,
            ),
            extraction_confidence=ConfidenceLevel.HIGH,
        )

        with patch.dict(os.environ, {"NVIDIA_API_KEY": "dummy-key"}, clear=False):
            with patch.object(NVIDIAExtractor, "extract", new_callable=AsyncMock) as mock_extract:
                mock_extract.return_value = mock_knowledge
                result = await extract_with_nvidia(
                    markdown="# Test",
                    source_url="https://mock.edu.ng",
                    institution_type="university",
                )
                assert result.institution.name == "Mock University"
                assert result.extraction_confidence == ConfidenceLevel.HIGH
