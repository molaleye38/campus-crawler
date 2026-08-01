"""Website Mapper for CKAP - discovers and prioritizes admission-related URLs."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

from .crawl4ai_client import Crawl4AIClient
from .models import InstitutionSeed
from .utils import polite_delay, safe_log

# ============================================================================
# URL CATEGORIES & PATTERNS
# ============================================================================

class URLCategory:
    ADMISSION_REQUIREMENTS = "admission_requirements"
    FEES = "fees"
    CUTOFFS = "cutoffs"
    PROGRAMS = "programs"
    CATCHMENT = "catchment"
    APPLICATION_PORTAL = "application_portal"
    POST_UTME = "post_utme"
    ACADEMIC_CALENDAR = "academic_calendar"
    GENERAL = "general"


CATEGORY_KEYWORDS = {
    URLCategory.ADMISSION_REQUIREMENTS: [
        "admission", "requirement", "utme", "cut.?off", "olevel", "o.?level",
        "subject", "combination", "entry", "qualification", "eligibility",
        "direct.?entry", "a.?level", "ijmb", "jupeb"
    ],
    URLCategory.FEES: [
        "fee", "tuition", "cost", "payment", "school.?fee", "acceptance",
        "hostel", "accommodation", "levy", "charge", "financial"
    ],
    URLCategory.CUTOFFS: [
        "cut.?off", "merit", "catchment", "elds", "departmental",
        "aggregate", "score", "mark", "point"
    ],
    URLCategory.PROGRAMS: [
        "programme", "program", "course", "faculty", "department",
        "degree", "undergraduate", "b.?sc", "b.?eng", "mb.?bs", "ll.?b",
        "b.?pharm", "b.?tech", "b.?ed", "nce", "nd", "hnd"
    ],
    URLCategory.CATCHMENT: [
        "catchment", "indigene", "state", "local.?government", "zone",
        "geographical", "elsd", "educationally.?less.?developed"
    ],
    URLCategory.APPLICATION_PORTAL: [
        "portal", "apply", "application", "registration", "jamb",
        "admission.?portal", "online", "student.?portal", "e.?portal"
    ],
    URLCategory.POST_UTME: [
        "post.?utme", "screening", "aptitude", "examination", "test",
        "interview", "exercise", "schedule", "venue", "past.?question"
    ],
    URLCategory.ACADEMIC_CALENDAR: [
        "calendar", "session", "semester", "resumption", "deadline",
        "important.?date", "timeline", "schedule"
    ],
}

CATEGORY_PRIORITY = {
    URLCategory.ADMISSION_REQUIREMENTS: 10,
    URLCategory.FEES: 9,
    URLCategory.CUTOFFS: 9,
    URLCategory.POST_UTME: 8,
    URLCategory.PROGRAMS: 7,
    URLCategory.CATCHMENT: 6,
    URLCategory.APPLICATION_PORTAL: 5,
    URLCategory.ACADEMIC_CALENDAR: 4,
    URLCategory.GENERAL: 1,
}

# Institution-specific URL patterns
INSTITUTION_PORTAL_PATTERNS = {
    "unilag": ["admissions.unilag.edu.ng", "unilag.edu.ng/admission"],
    "ui": ["admissions.ui.edu.ng", "ui.edu.ng/admission"],
    "unn": ["admissions.unn.edu.ng"],
    "buk": ["admissions.buk.edu.ng"],
    "abu": ["admissions.abu.edu.ng"],
    "fug": ["admissions.fug.edu.ng"],
    "fuk": ["admissions.fuk.edu.ng"],
    "fupre": ["admissions.fupre.edu.ng"],
    "fud": ["admissions.fud.edu.ng"],
    "fudma": ["admissions.fudma.edu.ng"],
    "ful": ["admissions.ful.edu.ng"],
    "fuoye": ["admissions.fuoye.edu.ng"],
    "fupa": ["admissions.fupa.edu.ng"],
    "fuyo": ["admissions.fuyo.edu.ng"],
}

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class DiscoveredURL:
    url: str
    category: str
    title: str | None = None
    snippet: str | None = None
    priority: int = 1
    source: str = "search"  # search, sitemap, crawl, known
    depth: int = 0
    parent_url: str | None = None

    def __hash__(self):
        return hash(self.url)

    def __eq__(self, other):
        if isinstance(other, DiscoveredURL):
            return self.url == other.url
        return False


@dataclass
class SiteMap:
    institution_name: str
    base_url: str
    discovered_urls: list[DiscoveredURL] = field(default_factory=list)
    sitemap_urls: list[str] = field(default_factory=list)
    robots_txt: str | None = None
    crawl_delay: float | None = None
    total_pages_estimated: int = 0


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _normalize_url(url: str, base: str | None = None) -> str | None:
    """Normalize and validate URL."""
    if not url:
        return None
    url = url.strip()
    if url.startswith("//"):
        url = "https:" + url
    elif not url.startswith(("http://", "https://")):
        if base:
            url = urljoin(base, url)
        else:
            url = "https://" + url
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return None
        # Remove fragments and common tracking params
        clean = parsed._replace(fragment="", query="").geturl()
        # Keep only http/https
        if parsed.scheme not in ("http", "https"):
            return None
        return clean
    except Exception:
        return None


def _get_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def _same_domain(url1: str, url2: str) -> bool:
    """Check if two URLs are on the same domain."""
    return _get_domain(url1) == _get_domain(url2)


def _categorize_url(url: str, title: str = "", snippet: str = "") -> str:
    """Categorize a URL based on keywords in URL, title, and snippet."""
    text = " ".join([url, title, snippet]).lower()
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if re.search(kw, text, re.IGNORECASE))
        if score > 0:
            scores[category] = score * CATEGORY_PRIORITY.get(category, 1)
    if not scores:
        return URLCategory.GENERAL
    return max(scores, key=scores.get)


def _calculate_priority(category: str, depth: int, is_known_portal: bool = False) -> int:
    """Calculate priority score for a URL."""
    base = CATEGORY_PRIORITY.get(category, 1)
    depth_penalty = depth * 2
    portal_bonus = 5 if is_known_portal else 0
    return max(1, base - depth_penalty + portal_bonus)


def _is_likely_admission_page(url: str, title: str = "", snippet: str = "") -> bool:
    """Quick check if URL is likely an admission-related page."""
    text = " ".join([url, title, snippet]).lower()
    admission_indicators = [
        "admission", "utme", "post.?utme", "cut.?off", "requirement",
        "fee", "programme", "course", "faculty", "catchment",
        "portal", "apply", "screening", "direct.?entry"
    ]
    return any(re.search(ind, text, re.IGNORECASE) for ind in admission_indicators)


def _extract_links_from_html(html: str, base_url: str) -> list[str]:
    """Extract all links from HTML content."""
    link_pattern = re.compile(r'<a\s+[^>]*href=["\']([^"\']+)["\']', re.IGNORECASE)
    raw_links = link_pattern.findall(html)
    normalized = []
    for link in raw_links:
        norm = _normalize_url(link, base_url)
        if norm and _same_domain(norm, base_url):
            normalized.append(norm)
    return list(set(normalized))


def _get_institution_short_name(name: str) -> str:
    """Generate short name for portal pattern matching."""
    name = name.lower()
    # Common abbreviations
    abbrev = {
        "university of lagos": "unilag",
        "university of ibadan": "ui",
        "obafemi awolowo university": "oau",
        "ahmad bello university": "abu",
        "university of nigeria": "unn",
        "bayero university": "buk",
        "federal university of technology": "fut",
        "federal university": "fu",
        "state university": "su",
        "polytechnic": "poly",
        "college of education": "coe",
    }
    for full, short in abbrev.items():
        if full in name:
            return short
    # Default: first word + first letters of other words
    words = name.split()
    if len(words) == 1:
        return words[0][:8]
    return words[0][:4] + "".join(w[0] for w in words[1:3])


# ============================================================================
# WEBSITE MAPPER CLASS
# ============================================================================

class WebsiteMapper:
    """Maps institution websites to discover admission-related URLs."""
    
    def __init__(
        self,
        client: Crawl4AIClient,
        max_depth: int = 2,
        max_pages_per_category: int = 5,
        max_total_pages: int = 30,
    ):
        self.client = client
        self.max_depth = max_depth
        self.max_pages_per_category = max_pages_per_category
        self.max_total_pages = max_total_pages
        self._visited: set[str] = set()
        self._discovered: list[DiscoveredURL] = []
    
    async def map_institution(self, seed: InstitutionSeed) -> SiteMap:
        """Main entry point: map an institution's website for admission URLs."""
        self._visited.clear()
        self._discovered.clear()
        
        base_url = seed.website or self._guess_base_url(seed)
        if not base_url:
            safe_log("mapper_no_base_url", name=seed.name)
            return SiteMap(institution_name=seed.name, base_url="")
        
        site_map = SiteMap(institution_name=seed.name, base_url=base_url)
        
        # 1. Check robots.txt
        await self._fetch_robots_txt(site_map)
        
        # 2. Try sitemap.xml
        await self._fetch_sitemap(site_map)
        
        # 3. Search for known admission portal patterns
        await self._search_known_portals(seed, site_map)
        
        # 4. DDG search for admission-related pages
        await self._search_admission_pages(seed, site_map)
        
        # 5. Crawl discovered URLs to find more (limited depth)
        await self._crawl_for_more_urls(site_map)
        
        # 6. Deduplicate and prioritize
        site_map.discovered_urls = self._prioritize_urls(site_map.discovered_urls)
        
        safe_log("mapper_complete", name=seed.name, urls=len(site_map.discovered_urls))
        return site_map
    
    def _guess_base_url(self, seed: InstitutionSeed) -> str | None:
        """Guess base URL from institution name if not provided."""
        if seed.website:
            return seed.website
        short = _get_institution_short_name(seed.name)
        # Try common Nigerian university patterns
        patterns = [
            f"https://{short}.edu.ng",
            f"https://www.{short}.edu.ng",
            f"https://{short}university.edu.ng",
        ]
        return patterns[0]  # Return first as guess; will be validated during search
    
    async def _fetch_robots_txt(self, site_map: SiteMap) -> None:
        """Fetch and parse robots.txt for crawl delays."""
        robots_url = urljoin(site_map.base_url, "/robots.txt")
        try:
            md = await self.client.scrape(robots_url)
            if md:
                site_map.robots_txt = md
                # Parse crawl-delay
                for line in md.split("\n"):
                    if "crawl-delay" in line.lower():
                        try:
                            delay = float(line.split(":")[1].strip())
                            site_map.crawl_delay = delay
                        except Exception:
                            pass
        except Exception:
            pass
    
    async def _fetch_sitemap(self, site_map: SiteMap) -> None:
        """Fetch and parse sitemap.xml."""
        sitemap_urls = [
            urljoin(site_map.base_url, "/sitemap.xml"),
            urljoin(site_map.base_url, "/sitemap_index.xml"),
            urljoin(site_map.base_url, "/sitemap/sitemap.xml"),
        ]
        for sm_url in sitemap_urls:
            try:
                md = await self.client.scrape(sm_url)
                if md and ("<urlset" in md or "<sitemapindex" in md):
                    site_map.sitemap_urls.append(sm_url)
                    # Extract URLs from sitemap
                    urls = re.findall(r"<loc>([^<]+)</loc>", md)
                    for u in urls:
                        norm = _normalize_url(u, site_map.base_url)
                        if norm:
                            site_map.discovered_urls.append(DiscoveredURL(
                                url=norm,
                                category=URLCategory.GENERAL,
                                source="sitemap",
                                priority=2,
                            ))
                    break
            except Exception:
                continue
    
    async def _search_known_portals(self, seed: InstitutionSeed, site_map: SiteMap) -> None:
        """Search for known admission portal patterns."""
        short = _get_institution_short_name(seed.name)
        patterns = INSTITUTION_PORTAL_PATTERNS.get(short, [])
        
        # Add common portal patterns
        base = site_map.base_url
        if base:
            domain = _get_domain(base)
            patterns.extend([
                f"https://admissions.{domain}",
                f"https://admission.{domain}",
                f"https://apply.{domain}",
                f"https://portal.{domain}",
                f"https://{domain}/admission",
                f"https://{domain}/admissions",
                f"https://{domain}/apply",
            ])
        
        for pattern in patterns:
            norm = _normalize_url(pattern, site_map.base_url)
            if norm and norm not in self._visited:
                self._visited.add(norm)
                site_map.discovered_urls.append(DiscoveredURL(
                    url=norm,
                    category=URLCategory.APPLICATION_PORTAL,
                    source="known_pattern",
                    priority=_calculate_priority(URLCategory.APPLICATION_PORTAL, 0, True),
                ))
    
    async def _search_admission_pages(self, seed: InstitutionSeed, site_map: SiteMap) -> None:
        """Search for admission-related pages via DDG."""
        queries = self._build_search_queries(seed)
        
        for query in queries:
            try:
                hits = await self.client.search(query, limit=10, scrape_contents=False)
                for hit in hits:
                    norm = _normalize_url(hit.url, site_map.base_url)
                    if not norm or norm in self._visited:
                        continue
                    if not _is_likely_admission_page(norm, hit.title or "", hit.snippet or ""):
                        continue
                    self._visited.add(norm)
                    category = _categorize_url(norm, hit.title or "", hit.snippet or "")
                    site_map.discovered_urls.append(DiscoveredURL(
                        url=norm,
                        category=category,
                        title=hit.title,
                        snippet=hit.snippet,
                        priority=_calculate_priority(category, 0),
                        source="search",
                    ))
            except Exception as e:
                safe_log("mapper_search_error", query=query, error=str(e))
            await polite_delay()
    
    def _build_search_queries(self, seed: InstitutionSeed) -> list[str]:
        """Build targeted search queries for admission pages."""
        name = seed.name
        short = _get_institution_short_name(name)
        queries = [
            f"{name} admission requirements UTME cut off mark",
            f"{name} school fees tuition 2025 2026",
            f"{name} post UTME screening form date",
            f"{name} catchment area ELDS states",
            f"{name} courses programmes faculty department",
            f"{name} admission portal apply online",
            f"{name} direct entry requirements A level JUPEB",
            f"{name} aggregate formula calculation",
            f"{name} jamb brochure courses",
            f"{short} admission requirements",
            f"{short} fees schedule",
            f"{short} cut off marks",
        ]
        return queries
    
    async def _crawl_for_more_urls(self, site_map: SiteMap) -> None:
        """Crawl high-priority discovered URLs to find more admission links."""
        # Sort by priority and take top URLs
        candidates = sorted(site_map.discovered_urls, key=lambda x: -x.priority)
        crawled = 0
        
        for disc_url in candidates:
            if crawled >= self.max_total_pages:
                break
            if disc_url.depth >= self.max_depth:
                continue
            if disc_url.url in self._visited and disc_url.source == "crawl":
                continue
            
            try:
                md = await self.client.scrape(disc_url.url)
                if not md:
                    continue
                
                # Extract links from page
                links = _extract_links_from_html(md, disc_url.url)
                for link in links:
                    if link in self._visited:
                        continue
                    if not _is_likely_admission_page(link):
                        continue
                    
                    self._visited.add(link)
                    category = _categorize_url(link)
                    new_disc = DiscoveredURL(
                        url=link,
                        category=category,
                        priority=_calculate_priority(category, disc_url.depth + 1),
                        source="crawl",
                        depth=disc_url.depth + 1,
                        parent_url=disc_url.url,
                    )
                    site_map.discovered_urls.append(new_disc)
                    crawled += 1
                    
            except Exception as e:
                safe_log("mapper_crawl_error", url=disc_url.url, error=str(e))
            
            await polite_delay()
    
    def _prioritize_urls(self, urls: list[DiscoveredURL]) -> list[DiscoveredURL]:
        """Deduplicate and prioritize URLs, limiting per category."""
        seen = set()
        by_category: dict[str, list[DiscoveredURL]] = {}
        
        for u in urls:
            if u.url in seen:
                continue
            seen.add(u.url)
            by_category.setdefault(u.category, []).append(u)
        
        result = []
        for category, cat_urls in by_category.items():
            # Sort by priority descending
            cat_urls.sort(key=lambda x: -x.priority)
            limit = self.max_pages_per_category
            if category in (URLCategory.ADMISSION_REQUIREMENTS, URLCategory.FEES, URLCategory.CUTOFFS):
                limit = self.max_pages_per_category + 2
            result.extend(cat_urls[:limit])
        
        # Sort overall by priority
        result.sort(key=lambda x: -x.priority)
        return result[:self.max_total_pages]


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def map_institution_website(
    seed: InstitutionSeed,
    client: Crawl4AIClient | None = None,
    max_depth: int = 2,
    max_pages_per_category: int = 5,
    max_total_pages: int = 30,
) -> SiteMap:
    """Convenience function to map a single institution."""
    owns_client = client is None
    if owns_client:
        client = Crawl4AIClient()
        await client.start()
    
    try:
        mapper = WebsiteMapper(
            client=client,
            max_depth=max_depth,
            max_pages_per_category=max_pages_per_category,
            max_total_pages=max_total_pages,
        )
        return await mapper.map_institution(seed)
    finally:
        if owns_client:
            await client.aclose()


async def map_multiple_institutions(
    seeds: list[InstitutionSeed],
    max_concurrent: int = 3,
    **mapper_kwargs,
) -> dict[str, SiteMap]:
    """Map multiple institutions with concurrency control."""
    semaphore = asyncio.Semaphore(max_concurrent)
    client = Crawl4AIClient()
    await client.start()
    
    async def map_one(seed: InstitutionSeed) -> tuple[str, SiteMap]:
        async with semaphore:
            mapper = WebsiteMapper(client=client, **mapper_kwargs)
            return seed.name, await mapper.map_institution(seed)
    
    try:
        tasks = [map_one(seed) for seed in seeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        output = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                safe_log("mapper_batch_error", name=seeds[i].name, error=str(result))
                output[seeds[i].name] = SiteMap(institution_name=seeds[i].name, base_url=seeds[i].website or "")
            else:
                name, site_map = result
                output[name] = site_map
        return output
    finally:
        await client.aclose()


# ============================================================================
# URL FILTERING FOR SCRAPER
# ============================================================================

def filter_urls_for_scraping(
    site_map: SiteMap,
    categories: list[str] | None = None,
    max_urls: int = 10,
) -> list[str]:
    """Extract URLs from SiteMap for the scraper pipeline."""
    if categories is None:
        categories = [
            URLCategory.ADMISSION_REQUIREMENTS,
            URLCategory.FEES,
            URLCategory.CUTOFFS,
            URLCategory.POST_UTME,
            URLCategory.PROGRAMS,
            URLCategory.CATCHMENT,
            URLCategory.APPLICATION_PORTAL,
        ]
    
    urls = []
    for cat in categories:
        cat_urls = [u.url for u in site_map.discovered_urls if u.category == cat]
        urls.extend(cat_urls[:max_urls // len(categories) + 1])
    
    return urls[:max_urls]


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__file__).rsplit("/", 3)[0] if "/" in __file__ else ".")
    
    async def test():
        from naija_admissions.models import InstitutionSeed, InstitutionType, OwnershipType
        
        seed = InstitutionSeed(
            name="University of Lagos",
            institution_type=InstitutionType.UNIVERSITY,
            type=OwnershipType.FEDERAL,
            state="Lagos",
            website="https://unilag.edu.ng",
        )
        
        site_map = await map_institution_website(seed)
        print(f"Mapped {site_map.institution_name}")
        print(f"Base URL: {site_map.base_url}")
        print(f"Discovered {len(site_map.discovered_urls)} URLs")
        
        for cat in [URLCategory.ADMISSION_REQUIREMENTS, URLCategory.FEES, URLCategory.CUTOFFS, URLCategory.PROGRAMS]:
            cat_urls = [u for u in site_map.discovered_urls if u.category == cat]
            if cat_urls:
                print(f"\n{cat} ({len(cat_urls)}):")
                for u in cat_urls[:3]:
                    print(f"  [{u.priority}] {u.url} - {u.title or 'No title'}")
        
        # Filter for scraper
        scrape_urls = filter_urls_for_scraping(site_map, max_urls=8)
        print(f"\nURLs for scraping ({len(scrape_urls)}):")
        for url in scrape_urls:
            print(f"  {url}")
    
    asyncio.run(test())