"""JAMB Brochure Spider.

Crawls jamb.gov.ng/ibass to extract programme requirements, UTME subject
combinations, O-Level requirements, and cut-off marks per course per institution.

Output: data/scrapy_data/jamb_programs.jsonlines
"""

from __future__ import annotations

import re as _re
from typing import Any

import scrapy


class JambBrochureSpider(scrapy.Spider):
    name = "jamb_spider"
    allowed_domains = ["jamb.gov.ng"]
    start_urls = [
        "https://www.jamb.gov.ng/ibass",
    ]

    custom_settings = {
        "FEEDS": {
            "data/scrapy_data/jamb_programs.jsonl": {"format": "jsonlines"},
        },
    }

    def parse(self, response: Any) -> Any:
        """Parse the JAMB IBASS institution listing page.

        The IBASS page has a table or grid of institutions with links to
        individual programme pages. We extract those links here.
        """
        self.logger.info("Parsing JAMB IBASS page: %s", response.url)

        links = response.css("a[href*='ibass']::attr(href)").getall()

        if not links:
            links = response.css(
                "a[href*='ibass'], a[href*='brochure'], a[href*='course'], "
                "a[href*='programme']"
            ).css("::attr(href)").getall()

        seen = set()
        for link in links:
            url = response.urljoin(link)
            if url in seen:
                continue
            seen.add(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_program_page,
                meta={"dont_redirect": True},
            )

    def parse_program_page(self, response: Any) -> Any:
        """Parse a single institution programme listing page.

        Typical input: A page listing all courses and their admission
        requirements for one institution as a table.
        """
        institution_name = self._extract_institution_name(response)

        rows = response.css("table tr")
        if not rows:
            rows = response.css(".ibass-table tr, .programme-table tr, .course-list tr")

        programmes: list[dict[str, Any]] = []
        for row in rows:
            cells = row.css("td::text, th::text").getall()
            if not cells or len(cells) < 2:
                continue

            programme = cells[0].strip() if len(cells) > 0 else ""
            utme_subjects = cells[1].strip() if len(cells) > 1 else ""
            olevel_info = cells[2].strip() if len(cells) > 2 else ""
            cutoff_raw = cells[3].strip() if len(cells) > 3 else ""

            if not programme or programme.lower() in ("programme", "course", "program", "s/n"):
                continue

            record = {
                "institution": institution_name,
                "programme": programme,
                "utme_subjects_raw": utme_subjects,
                "olevel_requirements_raw": olevel_info,
                "cutoff": self._parse_cutoff(cutoff_raw),
                "source_url": response.url,
            }
            programmes.append(record)

        if programmes:
            self.logger.info(
                "Extracted %d programmes for %s from %s",
                len(programmes), institution_name, response.url,
            )

        return programmes

    def _extract_institution_name(self, response: Any) -> str:
        """Try multiple selectors to find the university/polytechnic name."""
        name = response.css(
            "h1::text, .inst-name::text, .institution-name::text, caption::text"
        ).get()
        if name:
            return name.strip()

        title = response.css("title::text").get() or ""
        for sep in ("-", "|", ",", "\u2013", "\u2014"):
            if sep in title:
                parts = title.rsplit(sep, 1)
                candidate = parts[-1].strip()
                if len(candidate) > 3 and "JAMB" not in candidate.upper():
                    return candidate
        return ""

    def _parse_cutoff(self, raw: str) -> int | None:
        """Parse a UTME cutoff from a raw string like '200'."""
        digits = _re.findall(r"\d+", raw)
        if digits:
            val = int(digits[0])
            if 100 <= val <= 400:
                return val
        return None