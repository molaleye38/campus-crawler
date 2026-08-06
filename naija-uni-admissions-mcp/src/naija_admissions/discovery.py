"""Discovery module for CKAP — enriches the institution seed list from official regulatory sources.

Connectors:
    NUCConnector   — National Universities Commission (federal, state, private universities)
    NBTEConnector  — National Board for Technical Education (polytechnics, monotechnics, IEIs)
    NCCEConnector  — National Commission for Colleges of Education
    NMCNConnector  — Nursing and Midwifery Council of Nigeria (nursing schools)
    JAMBConnector  — JAMB IBASS (JAMB codes, programme requirements)

Each connector returns a list of DiscoveredInstitution dataclass objects.
run_discovery() runs all connectors, merges results, and deduplicates.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredInstitution:
    name: str
    institution_type: str
    ownership_type: str
    state: str | None = None
    website: str | None = None
    year_established: int | None = None
    contact_email: str | None = None
    phone: str | None = None
    address: str | None = None
    jamb_code: str | None = None
    accreditation_body: str | None = None
    source_url: str | None = None

    def matches_seed(self, seed_name: str) -> bool:
        s1 = self.name.lower().strip()
        s2 = seed_name.lower().strip()
        return s1 == s2 or s1 in s2 or s2 in s1


NUC_FEDERAL_URL = "https://www.nuc.edu.ng/nigerian-univerisities/federal-univeristies/"
NUC_STATE_URL = "https://www.nuc.edu.ng/nigerian-univerisities/state-univerisity/"
NUC_PRIVATE_URL = "https://www.nuc.edu.ng/nigerian-univerisities/private-univeristies/"

NCCE_URL = "https://ncce.gov.ng/AccreditedColleges"

NBTE_URL = "https://net.nbte.gov.ng"
NBTE_FALLBACK_URL = "https://www.nbte.gov.ng"

NMCN_SCHOOLS_PAGE = "https://nmcn.gov.ng/apschool.html"
NMCN_PDF_URL = "https://nmcn.gov.ng/docs/List_of_Approved_Schools_December_2025.pdf"

JAMB_IBASS_URL = "https://ibass.jamb.gov.ng"

_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "discovery_cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)

_NUC_ROW_RE = re.compile(
    r"\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(?:Prof\.?|Dr\.?|Mr\.?|Mrs\.?|Miss)?\s*[^|]+\s*"
    r"\|\s*<?\s*(https?://[^\s|>]+)>?\s*\|\s*(\d{4})\s*\|",
    re.MULTILINE,
)

_NCCE_ROW_RE = re.compile(
    r"\|\s*(\d+)\s*\|\s*(.+?)(?:\n\s*OPEN)?\s*\|"
    r"\s*[^|]*\|"
    r"\s*([^|]+)\|"
    r"\s*([^|]+)\|"
    r"\s*([^|]*)\|",
    re.MULTILINE,
)

_NUC_PAGINATION_RE = re.compile(r"Showing \d+ to \d+ of (\d+) entries")
_NUC_PAGE_LINKS_RE = re.compile(r"‹((\d+)*)›")


def _normalize_url(url: str | None) -> str | None:
    if not url or not url.strip():
        return None
    url = url.strip().rstrip("/")
    if not url.startswith("http"):
        url = "https://" + url
    return url


def _extract_state_from_name(name: str) -> str | None:
    state_patterns = [
        r",\s*([^,]+?)\s*$",
        r",\s*([^,]+?)\s+State\s*$",
    ]
    for pattern in state_patterns:
        m = re.search(pattern, name, re.IGNORECASE)
        if m:
            state = m.group(1).strip().rstrip(".")
            if len(state) > 2 and state.lower() not in ("state", "nigeria"):
                return state
    return None


async def _fetch_markdown(url: str, timeout: int = 60) -> str | None:
    try:
        from crawl4ai import AsyncWebCrawler
        from crawl4ai.async_configs import CacheMode, CrawlerRunConfig

        async with AsyncWebCrawler() as crawler:
            cfg = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, word_count_threshold=5)
            result = await crawler.arun(url=url, config=cfg)
            return result.markdown if result.markdown else None
    except Exception as e:
        logger.error(f"Crawl4AI failed for {url}: {e}")
        return None


async def _fetch_html(url: str, timeout: int = 30) -> str | None:
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml",
            },
            follow_redirects=True,
        ) as client:
            r = await client.get(url)
            r.raise_for_status()
            return r.text
    except Exception as e:
        logger.error(f"httpx failed for {url}: {e}")
        return None


async def _download_pdf(url: str, dest: Path, timeout: int = 120) -> bool:
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0"},
            follow_redirects=True,
        ) as client:
            r = await client.get(url)
            r.raise_for_status()
            dest.write_bytes(r.content)
            return True
    except Exception as e:
        logger.error(f"PDF download failed for {url}: {e}")
        return False


def _parse_nuc_table(markdown: str, ownership: str, source_url: str) -> list[DiscoveredInstitution]:
    rows = []
    for m in _NUC_ROW_RE.finditer(markdown):
        _, name, website, year = m.group(1), m.group(2).strip(), m.group(3).strip(), int(m.group(4))
        website = _normalize_url(website)
        state = _extract_state_from_name(name)
        name = re.sub(r",\s*,?", ",", name).strip().rstrip(",")
        rows.append(DiscoveredInstitution(
            name=name,
            institution_type="university",
            ownership_type=ownership,
            state=state,
            website=website,
            year_established=year,
            accreditation_body="NUC",
            source_url=source_url,
        ))
    return rows


def _parse_ncce_table(markdown: str, source_url: str) -> list[DiscoveredInstitution]:
    rows = []
    for m in _NCCE_ROW_RE.finditer(markdown):
        _, raw_name, Ownership, state, website_str = (
            m.group(1), m.group(2).strip(), m.group(3).strip(), m.group(4).strip(), m.group(5).strip()
        )
        Ownership_lower = Ownership.lower()
        if "federal" in Ownership_lower:
            own = "federal"
        elif "state" in Ownership_lower:
            own = "state"
        elif "private" in Ownership_lower:
            own = "private"
        else:
            own = "state"

        if "polytechnic" in Ownership_lower:
            inst_type = "polytechnic"
        else:
            inst_type = "college_of_education"

        website = _normalize_url(website_str) if website_str else None
        if website and "ncce.gov.ng" in website:
            website = None

        name = raw_name.replace("OPEN", "").strip().rstrip(",")
        if not name:
            continue

        rows.append(DiscoveredInstitution(
            name=name,
            institution_type=inst_type,
            ownership_type=own,
            state=state if state and state.lower() != "none" else None,
            website=website,
            accreditation_body="NCCE",
            source_url=source_url,
        ))
    return rows


class NUCConnector:
    async def discover(self) -> list[DiscoveredInstitution]:
        all_insts = []
        for url, ownership in [
            (NUC_FEDERAL_URL, "federal"),
            (NUC_STATE_URL, "state"),
            (NUC_PRIVATE_URL, "private"),
        ]:
            logger.info(f"NUC: fetching {ownership} universities from {url}")
            md = await _fetch_markdown(url)
            if not md:
                logger.warning(f"NUC: failed to fetch {url}")
                continue

            page_insts = _parse_nuc_table(md, ownership, url)
            all_insts.extend(page_insts)
            logger.info(f"NUC: parsed {len(page_insts)} {ownership} universities from page 1")

            total_match = _NUC_PAGINATION_RE.search(md)
            if total_match:
                total = int(total_match.group(1))
                if total > len(page_insts):
                    page_links = _NUC_PAGE_LINKS_RE.findall(md)
                    page_nums = set()
                    for pg in page_links:
                        for num_str in re.findall(r"\d", pg[0] if isinstance(pg, tuple) else pg):
                            page_nums.add(int(num_str))

                    for page_num in sorted(page_nums):
                        if page_num <= 1:
                            continue
                        page_url = f"{url}page/{page_num}/" if url.endswith("/") else f"{url}/page/{page_num}/"
                        md2 = await _fetch_markdown(page_url)
                        if md2:
                            page2_insts = _parse_nuc_table(md2, ownership, page_url)
                            all_insts.extend(page2_insts)
                            logger.info(f"NUC: parsed {len(page2_insts)} {ownership} universities from page {page_num}")

        return all_insts


class NBTEConnector:
    async def discover(self) -> list[DiscoveredInstitution]:
        for url in [NBTE_URL, NBTE_FALLBACK_URL]:
            md = await _fetch_markdown(url)
            if md:
                parsed = _parse_nbte_table(md, url)
                if parsed:
                    logger.info(f"NBTE: parsed {len(parsed)} polytechnics from {url}")
                    return parsed
                logger.warning(f"NBTE: {url} reachable but parser returned 0 rows")

        logger.warning("NBTE: live source unavailable. Falling back to curated polytechnic seed list.")
        from .polytechnic_seed import polytechnics_to_discovered
        return [DiscoveredInstitution(**d) for d in polytechnics_to_discovered()]


_NBTE_ROW_RE = re.compile(
    r"\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|",
    re.MULTILINE,
)


def _parse_nbte_table(markdown: str, source_url: str) -> list[DiscoveredInstitution]:
    rows: list[DiscoveredInstitution] = []
    for m in _NBTE_ROW_RE.finditer(markdown):
        name = m.group(2).strip()
        state = m.group(3).strip()
        ownership_raw = m.group(4).strip().lower()
        website = _normalize_url(m.group(5).strip() or None)
        if not name or name.lower() in ("name", "polytechnic"):
            continue
        if "federal" in ownership_raw:
            ownership = "federal"
        elif "state" in ownership_raw:
            ownership = "state"
        elif "private" in ownership_raw:
            ownership = "private"
        else:
            ownership = "state"
        rows.append(DiscoveredInstitution(
            name=name,
            institution_type="polytechnic",
            ownership_type=ownership,
            state=state or None,
            website=website,
            accreditation_body="NBTE",
            source_url=source_url,
        ))
    return rows


class NCCEConnector:
    async def discover(self) -> list[DiscoveredInstitution]:
        logger.info(f"NCCE: fetching accredited colleges from {NCCE_URL}")
        md = await _fetch_markdown(NCCE_URL)
        if not md:
            logger.warning("NCCE: failed to fetch")
            return []
        insts = _parse_ncce_table(md, NCCE_URL)
        logger.info(f"NCCE: parsed {len(insts)} colleges")
        return insts


class NMCNConnector:
    async def discover(self) -> list[DiscoveredInstitution]:
        logger.info("NMCN: fetching approved nursing schools list")
        pdf_path = _CACHE_DIR / "nmcn_approved_schools.pdf"

        if not pdf_path.exists():
            ok = await _download_pdf(NMCN_PDF_URL, pdf_path)
            if not ok:
                logger.warning("NMCN: PDF download failed")
                return []

        try:
            import pdfplumber
        except ImportError:
            logger.warning("NMCN: pdfplumber not installed. Run: pip install pdfplumber")
            return []

        insts = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            if not row or len(row) < 3:
                                continue
                            name = row[1].strip() if row[1] else ""
                            state = row[2].strip() if row[2] else None if len(row) > 2 else None
                            if not name or name.lower() in ("name", "s/n", "school"):
                                continue
                            inst_type = "nursing_school"
                            if "midwif" in name.lower():
                                inst_type = "nursing_school"
                            insts.append(DiscoveredInstitution(
                                name=name,
                                institution_type=inst_type,
                                ownership_type="state",
                                state=state,
                                accreditation_body="NMCN",
                                source_url=NMCN_PDF_URL,
                            ))
        except Exception as e:
            logger.error(f"NMCN: PDF parsing failed: {e}")
            return []

        logger.info(f"NMCN: parsed {len(insts)} nursing institutions from PDF")
        return insts


class JAMBConnector:
    async def discover(self) -> list[DiscoveredInstitution]:
        logger.info("JAMB: IBASS portal requires authentication. Skipping automated discovery.")
        return []


def _dedupe(insts: list[DiscoveredInstitution]) -> list[DiscoveredInstitution]:
    seen = set()
    result = []
    for inst in insts:
        key = inst.name.lower().strip()
        if key not in seen:
            seen.add(key)
            result.append(inst)
    return result


async def run_discovery(
    connectors: list[str] | None = None,
    output_path: Path | None = None,
) -> list[DiscoveredInstitution]:
    if connectors is None:
        connectors = ["nuc", "ncce", "nmcn", "nbte", "jamb"]

    connector_map = {
        "nuc": NUCConnector,
        "nbte": NBTEConnector,
        "ncce": NCCEConnector,
        "nmcn": NMCNConnector,
        "jamb": JAMBConnector,
    }

    all_insts: list[DiscoveredInstitution] = []

    for name in connectors:
        cls = connector_map.get(name.lower())
        if not cls:
            logger.warning(f"Unknown connector: {name}")
            continue
        try:
            results = await cls().discover()
            all_insts.extend(results)
            logger.info(f"Connector '{name}': {len(results)} institutions discovered")
        except Exception as e:
            logger.error(f"Connector '{name}' failed: {e}")

    deduped = _dedupe(all_insts)
    logger.info(f"Total: {len(all_insts)} discovered, {len(deduped)} after dedup")

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([asdict(i) for i in deduped], f, indent=2, ensure_ascii=False)
        logger.info(f"Saved to {output_path}")

    return deduped


def write_discovery_output(insts: list[DiscoveredInstitution], path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump([asdict(i) for i in insts], f, indent=2, ensure_ascii=False)
    return p


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    output = _CACHE_DIR.parent / "discovered_institutions.json"
    results = asyncio.run(run_discovery(output_path=output))

    by_type = {}
    for inst in results:
        by_type.setdefault(inst.institution_type, 0)
        by_type[inst.institution_type] += 1

    print("\n=== Discovery Complete ===")
    print(f"Total institutions: {len(results)}")
    for t, count in sorted(by_type.items()):
        print(f"  {t}: {count}")
    with_website = sum(1 for i in results if i.website)
    print(f"  With website: {with_website}/{len(results)} ({100*with_website/len(results):.0f}%)")
    print(f"Saved to: {output}")
