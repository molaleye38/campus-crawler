"""Tests for website_mapper."""


from naija_admissions.website_mapper import (
    DiscoveredURL,
    SiteMap,
    URLCategory,
    _calculate_priority,
    _categorize_url,
    _extract_links_from_html,
    _get_domain,
    _get_institution_short_name,
    _is_likely_admission_page,
    _normalize_url,
    _same_domain,
    filter_urls_for_scraping,
)


class TestURLHelpers:
    """Test URL helper functions."""

    def test_normalize_url_https(self):
        assert _normalize_url("https://example.com/page") == "https://example.com/page"

    def test_normalize_url_http(self):
        assert _normalize_url("http://example.com") == "http://example.com"

    def test_normalize_url_relative_with_base(self):
        assert _normalize_url("/page", "https://example.com") == "https://example.com/page"

    def test_normalize_url_protocol_relative(self):
        assert _normalize_url("//example.com/page") == "https://example.com/page"

    def test_normalize_url_invalid_returns_none(self):
        assert _normalize_url("") is None
        assert _normalize_url(None) is None

    def test_normalize_url_strips_fragment(self):
        url = _normalize_url("https://example.com/page#section")
        assert url == "https://example.com/page"
        assert "section" not in (url or "")

    def test_get_domain(self):
        assert _get_domain("https://www.example.com") == "example.com"
        assert _get_domain("https://admissions.unilag.edu.ng") == "admissions.unilag.edu.ng"

    def test_same_domain_true(self):
        assert _same_domain("https://example.com/a", "https://example.com/b")

    def test_same_domain_false(self):
        assert not _same_domain("https://example.com", "https://other.com")


class TestURLCategorization:
    """Test URL categorization."""

    def test_admission_requirements_category(self):
        category = _categorize_url(
            "https://unilag.edu.ng/admission-requirements",
            "Admission Requirements",
            "UTME cut-off marks and O-Level subjects",
        )
        assert category == URLCategory.ADMISSION_REQUIREMENTS

    def test_fees_category(self):
        category = _categorize_url(
            "https://unilag.edu.ng/school-fees",
            "School Fees",
            "Tuition and other charges",
        )
        assert category == URLCategory.FEES

    def test_cutoffs_category(self):
        category = _categorize_url(
            "https://unilag.edu.ng/departmental-cut-off-marks",
            "Departmental Cut-off Marks",
            "Merit and catchment cutoffs",
        )
        assert category == URLCategory.CUTOFFS

    def test_programs_category(self):
        category = _categorize_url(
            "https://unilag.edu.ng/courses-programmes",
            "Courses and Programmes",
            "List of undergraduate programmes",
        )
        assert category == URLCategory.PROGRAMS

    def test_general_category_for_unknown(self):
        category = _categorize_url(
            "https://example.com/about",
            "About Us",
            "History of the university",
        )
        assert category == URLCategory.GENERAL

    def test_priority_admission_requirements_high(self):
        priority = _calculate_priority(URLCategory.ADMISSION_REQUIREMENTS, 0)
        assert priority >= 10

    def test_priority_decreases_with_depth(self):
        shallow = _calculate_priority(URLCategory.ADMISSION_REQUIREMENTS, 0)
        deep = _calculate_priority(URLCategory.ADMISSION_REQUIREMENTS, 3)
        assert deep < shallow

    def test_priority_known_portal_bonus(self):
        normal = _calculate_priority(URLCategory.APPLICATION_PORTAL, 0, False)
        known = _calculate_priority(URLCategory.APPLICATION_PORTAL, 0, True)
        assert known > normal


class TestAdmissionPageDetection:
    """Test admission page detection."""

    def test_admission_url_detected(self):
        assert _is_likely_admission_page("https://unilag.edu.ng/admissions")

    def test_fees_url_detected(self):
        assert _is_likely_admission_page("https://unilag.edu.ng/school-fees")

    def test_non_admission_url_not_detected(self):
        assert not _is_likely_admission_page("https://example.com/contact")

    def test_admission_in_title(self):
        assert _is_likely_admission_page("https://example.com", title="Admission Requirements 2025")

    def test_admission_in_snippet(self):
        assert _is_likely_admission_page("https://example.com", snippet="Post-UTME screening form")


class TestLinkExtraction:
    """Test HTML link extraction."""

    def test_extract_links_basic(self):
        html = '<a href="/admissions">Admissions</a><a href="/fees">Fees</a>'
        links = _extract_links_from_html(html, "https://example.com")
        assert "https://example.com/admissions" in links
        assert "https://example.com/fees" in links

    def test_extract_links_filters_external(self):
        html = '<a href="/local">Local</a><a href="https://other.com/external">External</a>'
        links = _extract_links_from_html(html, "https://example.com")
        assert "https://example.com/local" in links
        assert "https://other.com/external" not in links

    def test_extract_links_deduplicates(self):
        html = '<a href="/page">Page</a><a href="/page">Page Again</a>'
        links = _extract_links_from_html(html, "https://example.com")
        assert len(links) == 1


class TestInstitutionShortName:
    """Test institution short name generation."""

    def test_university_of_lagos(self):
        assert _get_institution_short_name("University of Lagos") == "unilag"

    def test_university_of_ibadan(self):
        assert _get_institution_short_name("University of Ibadan") == "ui"

    def test_federal_university_of_technology(self):
        assert _get_institution_short_name("Federal University of Technology") == "fut"

    def test_polytechnic(self):
        assert _get_institution_short_name("Lagos State Polytechnic") == "poly"


class TestSiteMapDataclass:
    """Test SiteMap and DiscoveredURL dataclasses."""

    def test_sitemap_defaults(self):
        sm = SiteMap(institution_name="Test", base_url="https://test.edu.ng")
        assert sm.discovered_urls == []
        assert sm.sitemap_urls == []
        assert sm.robots_txt is None

    def test_discovered_url_hash(self):
        u1 = DiscoveredURL(url="https://example.com", category=URLCategory.GENERAL)
        u2 = DiscoveredURL(url="https://example.com", category=URLCategory.FEES)
        assert u1 == u2
        assert hash(u1) == hash(u2)

    def test_discovered_url_neq_different_url(self):
        u1 = DiscoveredURL(url="https://example.com", category=URLCategory.GENERAL)
        u2 = DiscoveredURL(url="https://other.com", category=URLCategory.GENERAL)
        assert u1 != u2


class TestFilterURLsForScraping:
    """Test filter_urls_for_scraping."""

    def test_returns_urls_from_all_categories(self):
        sm = SiteMap(institution_name="Test", base_url="https://test.edu.ng")
        sm.discovered_urls = [
            DiscoveredURL(url="https://test.edu.ng/admissions", category=URLCategory.ADMISSION_REQUIREMENTS, priority=10),
            DiscoveredURL(url="https://test.edu.ng/fees", category=URLCategory.FEES, priority=9),
            DiscoveredURL(url="https://test.edu.ng/cutoffs", category=URLCategory.CUTOFFS, priority=9),
            DiscoveredURL(url="https://test.edu.ng/programs", category=URLCategory.PROGRAMS, priority=7),
        ]
        urls = filter_urls_for_scraping(sm, max_urls=10)
        assert "https://test.edu.ng/admissions" in urls
        assert "https://test.edu.ng/fees" in urls
        assert "https://test.edu.ng/cutoffs" in urls
        assert "https://test.edu.ng/programs" in urls

    def test_respects_max_urls_limit(self):
        sm = SiteMap(institution_name="Test", base_url="https://test.edu.ng")
        sm.discovered_urls = [
            DiscoveredURL(url=f"https://test.edu.ng/page{i}", category=URLCategory.GENERAL, priority=1)
            for i in range(20)
        ]
        urls = filter_urls_for_scraping(sm, max_urls=5)
        assert len(urls) <= 5

    def test_specific_categories_only(self):
        sm = SiteMap(institution_name="Test", base_url="https://test.edu.ng")
        sm.discovered_urls = [
            DiscoveredURL(url="https://test.edu.ng/admissions", category=URLCategory.ADMISSION_REQUIREMENTS, priority=10),
            DiscoveredURL(url="https://test.edu.ng/fees", category=URLCategory.FEES, priority=9),
            DiscoveredURL(url="https://test.edu.ng/about", category=URLCategory.GENERAL, priority=1),
        ]
        urls = filter_urls_for_scraping(sm, categories=[URLCategory.ADMISSION_REQUIREMENTS], max_urls=5)
        assert "https://test.edu.ng/admissions" in urls
        assert "https://test.edu.ng/about" not in urls
