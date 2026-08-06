"""Portal Spider — LinkExtractor-based crawler for institution admission portals.

Uses the seed list from institutions.py to crawl each school's admission pages
and extract tables, lists, and forms (tuition, requirements, application steps).

Output: data/scrapy_data/portal_admissions.jsonlines
"""

from __future__ import annotations

from typing import Any

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class PortalSpider(CrawlSpider):
    name = "portal_spider"
    allowed_domains = []  # Populated dynamically from seeds
    start_urls = []  # Populated dynamically from seeds

    rules = (
        Rule(
            LinkExtractor(
                allow=r"(admission|apply|portal|fees|requirements|cut[- ]?off|utme|post[- ]?utme)",
                deny=(r"pdf$", r"doc$", r"jpg$", r"png$", r"zip$", r"rar$"),
                restrict_xpaths=(
                    "//nav",
                    "//header",
                    "//main",
                    "//article",
                    "//div[contains(@class,'menu')]",
                    "//div[contains(@class,'nav')]",
                    "//ul",
                ),
            ),
            callback="parse_page",
            follow=True,
        ),
    )

    custom_settings = {
        "FEEDS": {
            "data/scrapy_data/portal_admissions.jsonl": {"format": "jsonlines"},
        },
        "DEPTH_LIMIT": 3,
    }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._load_seeds()

    def _load_seeds(self) -> None:
        """Load institution seeds and build allowed_domains + start_urls."""
        try:
            import sys
            sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
            from src.naija_admissions.institutions import ALL_INSTITUTIONS

            urls = []
            domains = set()
            for seed in ALL_INSTITUTIONS:
                if seed.website:
                    urls.append(seed.website.rstrip("/"))
                    # Extract domain
                    from urllib.parse import urlparse
                    domain = urlparse(seed.website).netloc.lower()
                    if domain:
                        domains.add(domain)
                        domains.add("www." + domain)

            self.start_urls = urls[:50]  # Limit initial seeds for testing
            self.allowed_domains = list(domains)

            self.logger.info("PortalSpider: %d start URLs, %d domains",
                             len(self.start_urls), len(self.allowed_domains))
        except Exception as e:
            self.logger.warning("Could not load seeds: %s. Using fallback.", e)
            # Fallback: use major known domains
            self.start_urls = [
                "https://www.unilag.edu.ng",
                "https://www.abu.edu.ng",
                "https://www.uniben.edu",
                "https://www.ui.edu.ng",
                "https://www.unilorin.edu.ng",
            ]
            self.allowed_domains = [
                "unilag.edu.ng", "www.unilag.edu.ng",
                "abu.edu.ng", "www.abu.edu.ng",
                "uniben.edu", "www.uniben.edu",
                "ui.edu.ng", "www.ui.edu.ng",
                "unilorin.edu.ng", "www.unilorin.edu.ng",
            ]

    def parse_page(self, response: Any) -> Any:
        """Parse an admission-related page for structured content."""
        self.logger.info("Parsing portal page: %s", response.url)

        # Extract text content from main areas
        main_text = " ".join(
            response.css("main *::text, article *::text, .content *::text, "
                         "#content *::text, .post *::text, .entry *::text")
            .getall()
        ).strip()

        # Extract tables (fees, requirements, cutoffs)
        tables = []
        for table in response.css("table"):
            headers = [th.strip() for th in table.css("th::text").getall()]
            rows = []
            for row in table.css("tr"):
                cells = [td.strip() for td in row.css("td::text, th::text").getall()]
                if cells:
                    rows.append(cells)
            if rows:
                tables.append({"headers": headers, "rows": rows})

        # Extract lists (requirements, steps)
        lists = []
        for ul in response.css("ul, ol"):
            items = [li.strip() for li in ul.css("li::text").getall() if li.strip()]
            if items:
                lists.append(items)

        # Only yield if we found something admission-related
        content_keywords = (
            "admission", "requirement", "fee", "tuition", "cutoff",
            "utme", "post-utme", "olevel", "jamb", "apply", "portal",
        )
        full_text = (main_text + " " + str(tables) + " " + str(lists)).lower()
        if not any(kw in full_text for kw in content_keywords):
            return

        yield {
            "url": response.url,
            "title": response.css("title::text").get("").strip(),
            "main_text": main_text[:5000] if main_text else "",
            "tables": tables,
            "lists": lists,
            "depth": response.meta.get("depth", 0),
        }