"""Tests for prompt templates in extraction_models."""


from naija_admissions.extraction_models import (
    SYSTEM_PROMPT,
    build_user_prompt,
)


class TestSystemPrompt:
    """Test system prompt template."""

    def test_system_prompt_contains_nigerian_context(self):
        assert "Nigerian" in SYSTEM_PROMPT
        assert "tertiary" in SYSTEM_PROMPT.lower()

    def test_system_prompt_mentions_json(self):
        assert "JSON" in SYSTEM_PROMPT
        assert "ExtractedKnowledge" in SYSTEM_PROMPT

    def test_system_prompt_contains_extraction_rules(self):
        assert "hallucinate" in SYSTEM_PROMPT.lower()
        assert "Confidence" in SYSTEM_PROMPT

    def test_system_prompt_mentions_elds(self):
        assert "ELDS" in SYSTEM_PROMPT
        assert "Adamawa" in SYSTEM_PROMPT

    def test_system_prompt_lists_institution_types(self):
        assert "university" in SYSTEM_PROMPT.lower()
        assert "polytechnic" in SYSTEM_PROMPT.lower()
        assert "college_of_education" in SYSTEM_PROMPT.lower()

    def test_system_prompt_lists_degree_levels(self):
        assert "ND" in SYSTEM_PROMPT
        assert "HND" in SYSTEM_PROMPT
        assert "MBBS" in SYSTEM_PROMPT
        assert "LLB" in SYSTEM_PROMPT


class TestUserPrompt:
    """Test user prompt builder."""

    def test_basic_prompt(self):
        prompt = build_user_prompt(
            markdown_content="# Test Content",
            source_url="https://test.edu.ng",
            institution_type="university",
        )
        assert "Test Content" in prompt
        assert "https://test.edu.ng" in prompt
        assert "university" in prompt

    def test_includes_known_institution(self):
        prompt = build_user_prompt(
            markdown_content="# Test",
            source_url="https://test.edu.ng",
            institution_type="university",
            known_institution_name="University of Lagos",
        )
        assert "University of Lagos" in prompt

    def test_includes_academic_session(self):
        prompt = build_user_prompt(
            markdown_content="# Test",
            source_url="https://test.edu.ng",
            institution_type="university",
            academic_session="2025/2026",
        )
        assert "2025/2026" in prompt

    def test_truncates_long_content(self):
        long_content = "x" * 60000
        prompt = build_user_prompt(
            markdown_content=long_content,
            source_url="https://test.edu.ng",
            institution_type="university",
        )
        assert len(prompt) < 60000

    def test_handles_unknown_institution(self):
        prompt = build_user_prompt(
            markdown_content="# Test",
            source_url="https://test.edu.ng",
            institution_type="university",
            known_institution_name=None,
        )
        assert "Unknown" in prompt

    def test_prompt_format_has_source_marker(self):
        prompt = build_user_prompt(
            markdown_content="# Test",
            source_url="https://test.edu.ng",
            institution_type="university",
        )
        assert "SOURCE URL:" in prompt
        assert "INSTITUTION TYPE:" in prompt
        assert "ACADEMIC SESSION:" in prompt
        assert "CONTENT (Markdown):" in prompt
        assert "ExtractedKnowledge JSON" in prompt
