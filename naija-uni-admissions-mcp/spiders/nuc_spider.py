"""NUC Accreditation Spider.

Crawls nuc.edu.ng to extract accredited programmes per university.

Output: data/scrapy_data/nuc_programs.jsonlines
"""

from __future__ import annotations

import re as _re
from typing import Any

import scrapy


class NucAccreditationSpider(scrapy.Spider):
    name = "nuc_spider"
    allowed_domains = ["nuc.edu.ng"]
    start_urls = [
        "https://www.nuc.edu.ng/nigerian-univerisities/federal-univeristies/",
        "https://www.nuc.edu.ng/nigerian-univerisities/state-univerisity/",
        "https://www.nuc.edu.ng/nigerian-univerisities/private-univeristies/",
    ]

    custom_settings = {
        "FEEDS": {
            "data/scrapy_data/nuc_programs.jsonl": {"format": "jsonlines"},
        },
    }

    def parse(self, response: Any) -> Any:
        """Parse NUC university listing page — extract individual university links."""
        self.logger.info("Parsing NUC page: %s", response.url)

        # NUC lists universities with links to each institution's detail page
        links = response.css("a::attr(href)").getall()
        seen = set()

        for link in links:
            url = response.urljoin(link)
            # Only follow NUC detail pages, not external
            if "nuc.edu.ng" not in url:
                continue
            if url in seen:
                continue
            seen.add(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_institution_page,
            )

    def parse_institution_page(self, response: Any) -> Any:
        """Parse a single university's detail page for accredited programmes.

        NUC detail pages typically list:
        - University name (h1)
        - Type (federal/state/private)
        - Accredited programmes table (programme, accreditation status, expiry)
        """
        name = self._extract_name(response)
        owner_type = self._extract_ownership(response, response.url)

        rows = response.css("table tr, .accredited-table tr")
        if not rows:
            return

        programmes: list[dict] = []
        for row in rows:
            cells = row.css("td::text, th::text, td a::text").getall()
            if not cells or len(cells) < 1:
                continue

            programme = cells[0].strip() if len(cells) > 0 else ""
            status_raw = cells[1].strip() if len(cells) > 1 else "Full"
            expiry_raw = cells[2].strip() if len(cells) > 2 else ""

            if not programme or programme.lower() in ("programme", "course", "program", "s/n", "faculty"):
                continue

            record = {
                "institution": name,
                "ownership": owner_type,
                "programme": programme,
                "accreditation_status": status_raw,
                "accreditation_expiry": expiry_raw,
                "source_url": response.url,
            }
            programmes.append(record)

        if programmes:
            self.logger.info(
                "Extracted %d programmes for %s from %s",
                len(programmes), name, response.url,
            )

        return programmes

    def _extract_name(self, response: Any) -> str:
        name = response.css(
            "h1::text, .entry-title::text, .page-title::text, caption::text"
        ).get()
        return name.strip() if name else ""

    def _extract_ownership(self, response: Any, url: str) -> str:
        url_lower = url.lower()
        if "federal" in url_lower:
            return "federal"
        if "state" in url_lower:
            return "state"
        if "private" in url_lower:
            return "private"
        return "unknown"

    def _parse_expiry(self, raw: str) -> str:
        """Normalize date strings."""
        digits = _re.findall(r"\d{4}", raw)
        return digits[0] if digits else raw.strip()