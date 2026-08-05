from __future__ import annotations

import asyncio
import random
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote

import httpx
from crawl4ai import AsyncWebCrawler, CacheMode

from .utils import safe_log


@dataclass
class SearchHit:
    url: str
    title: str | None
    snippet: str | None
    content: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"url": self.url, "title": self.title, "snippet": _trunc_text(self.snippet, 500)}


def _trunc_text(s: str | None, n: int = 5000) -> str | None:
    if s is None:
        return None
    return s if len(s) <= n else s[: n - 1] + "\u2026"


class CrawlError(Exception):
    pass


_DDG_HTML_URL = "https://html.duckduckgo.com/html/"

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0",
]

_ACCEPT_LANGUAGES = [
    "en-US,en;q=0.9",
    "en-GB,en;q=0.9",
    "en-US,en;q=0.9,fr;q=0.8",
]


def _random_headers() -> dict[str, str]:
    return {
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": random.choice(_ACCEPT_LANGUAGES),
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Sec-CH-UA": '"Chromium";v="121", "Not A(Brand";v="99"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
    }


_MIN_DELAY_SEC = 1.5
_MAX_DELAY_SEC = 3.0
_MAX_RETRIES = 3
_BASE_BACKOFF_SEC = 5.0
_BACKOFF_CAP_SEC = 60.0
_SCRAPE_TIMEOUT_SEC = 20
_MAX_SCRAPE_RETRIES = 2
_PAGE_LOAD_TIMEOUT_MS = 15000
_BROWSER_RESET_EVERY = 25


_DDG_LINK_RE = re.compile(
    r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL
)
_DDG_SNIPPET_RE = re.compile(
    r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>', re.DOTALL
)
_STRIP_TAGS_RE = re.compile(r"<[^>]+>")
_RATE_LIMIT_MARKERS = (
    "anomaly",
    "rate limit",
    "too many requests",
    "blocked",
    "captcha",
    "Our systems have detected",
    "unusual traffic",
)


def _strip_html(s: str) -> str:
    s = _STRIP_TAGS_RE.sub("", s)
    s = s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    s = s.replace("&quot;", '"').replace("&#39;", "'")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _looks_like_rate_limit(html: str) -> bool:
    head = html[:8000].lower()
    return any(marker in head for marker in _RATE_LIMIT_MARKERS)


def _parse_ddg_html(html: str) -> list[SearchHit]:
    links = _DDG_LINK_RE.findall(html)
    snippets = _DDG_SNIPPET_RE.findall(html)
    hits: list[SearchHit] = []
    for i, (raw_url, raw_title) in enumerate(links):
        if "uddg=" in raw_url:
            m = re.search(r"uddg=([^&]+)", raw_url)
            url = unquote(m.group(1)) if m else raw_url
        elif raw_url.startswith("//"):
            url = "https:" + raw_url
        else:
            url = raw_url
        title = _strip_html(raw_title)
        snippet = _strip_html(snippets[i]) if i < len(snippets) else None
        if url and not url.startswith("javascript:"):
            hits.append(SearchHit(url=url, title=title, snippet=snippet))
        if len(hits) >= 10:
            break
    return hits


class Crawl4AIClient:
    def __init__(self, on_credits_used: callable | None = None):
        self._on_credits_used = on_credits_used
        self._http = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=15.0, read=30.0, write=15.0, pool=15.0),
            headers=_random_headers(),
            follow_redirects=True,
            http2=False,
        )
        self._crawler: AsyncWebCrawler | None = None
        self._last_search_at: float = 0.0
        self._scrape_count = 0

    async def __aenter__(self) -> Crawl4AIClient:
        await self.start()
        return self

    async def __aexit__(self, *exc) -> None:
        await self.aclose()

    async def start(self) -> None:
        if self._crawler is None:
            try:
                from crawl4ai import BrowserConfig
                browser_config = BrowserConfig(
                    browser_type="chromium",
                    headless=True,
                    verbose=False,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-images",
                        "--disable-gpu",
                        "--disable-blink-features=AutomationControlled",
                    ],
                )
                self._crawler = AsyncWebCrawler(config=browser_config)
            except Exception:
                self._crawler = AsyncWebCrawler(verbose=False)
            await self._crawler.__aenter__()

    async def reset_browser(self) -> None:
        await self.aclose()
        self._scrape_count = 0
        await self.start()

    async def aclose(self) -> None:
        if self._crawler is not None:
            try:
                await self._crawler.__aexit__(None, None, None)
            except Exception:
                pass
            self._crawler = None
        await self._http.aclose()

    async def _throttle_before_search(self) -> None:
        import time
        now = time.monotonic()
        wait = _MIN_DELAY_SEC - (now - self._last_search_at)
        wait += random.uniform(0, _MAX_DELAY_SEC - _MIN_DELAY_SEC)
        if wait > 0:
            await asyncio.sleep(wait)
        self._last_search_at = time.monotonic()

    async def _ddg_post(self, query: str) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                self._http.headers.update(_random_headers())
                r = await self._http.post(_DDG_HTML_URL, data={"q": query})
                if r.status_code == 429:
                    wait = min(_BACKOFF_CAP_SEC, _BASE_BACKOFF_SEC * (2 ** attempt))
                    wait += random.uniform(0, 2.0)
                    safe_log("ddg_rate_limited", query=query, attempt=attempt + 1, wait_sec=round(wait, 1))
                    await asyncio.sleep(wait)
                    continue
                if r.status_code in (403, 503):
                    wait = min(_BACKOFF_CAP_SEC, _BASE_BACKOFF_SEC * (2 ** attempt))
                    wait += random.uniform(0, 2.0)
                    safe_log("ddg_blocked", query=query, status=r.status_code, attempt=attempt + 1, wait_sec=round(wait, 1))
                    await asyncio.sleep(wait)
                    continue
                return r
            except (httpx.ConnectError, httpx.ReadError, httpx.WriteTimeout) as e:
                last_exc = e
                wait = min(_BACKOFF_CAP_SEC, _BASE_BACKOFF_SEC * (2 ** attempt))
                wait += random.uniform(0, 2.0)
                safe_log("ddg_network_error", query=query, attempt=attempt + 1, error=str(e), wait_sec=round(wait, 1))
                await asyncio.sleep(wait)
                continue
        if last_exc is not None:
            raise last_exc
        raise CrawlError(f"DDG search exhausted retries for query={query!r}")

    async def search(
        self,
        query: str,
        limit: int = 10,
        include_domains: list[str] | None = None,
        scrape_contents: bool = False,
    ) -> list[SearchHit]:
        await self._throttle_before_search()
        try:
            r = await self._ddg_post(query)
        except Exception as e:
            safe_log("ddg_search_failed", query=query, error=str(e))
            return []

        if _looks_like_rate_limit(r.text):
            safe_log("ddg_soft_rate_limit", query=query, html_len=len(r.text))
            return []

        r.raise_for_status()
        try:
            hits = _parse_ddg_html(r.text)
        except Exception as e:
            safe_log("ddg_parse_error", query=query, error=str(e))
            return []

        if include_domains:
            filtered: list[SearchHit] = []
            for h in hits:
                if any(d in h.url.lower() for d in include_domains):
                    filtered.append(h)
            hits = filtered

        hits = hits[:limit]
        if self._on_credits_used and hits:
            await self._on_credits_used(1)

        if scrape_contents and hits:
            for h in hits[:3]:
                md = await self.scrape(h.url)
                h.content = md
        return hits

    async def scrape(self, url: str, formats: list[str] | None = None, timeout_sec: int = _SCRAPE_TIMEOUT_SEC) -> str | None:
        if self._crawler is None:
            await self.start()

        if self._scrape_count and self._scrape_count % _BROWSER_RESET_EVERY == 0:
            await self.reset_browser()

        last_exc: Exception | None = None
        for attempt in range(_MAX_SCRAPE_RETRIES + 1):
            try:
                task = asyncio.wait_for(
                    self._crawler.arun(
                        url=url,
                        cache_mode=CacheMode.BYPASS,
                        excluded_tags=["nav", "footer", "header", "script", "style", "aside", "noscript"],
                        word_count_threshold=20,
                        page_timeout=_PAGE_LOAD_TIMEOUT_MS,
                    ),
                    timeout=timeout_sec,
                )
                result = await task
                self._scrape_count += 1
            except asyncio.TimeoutError:
                last_exc = asyncio.TimeoutError(f"Scrape timeout after {timeout_sec}s")
                safe_log("crawl4ai_scrape_timeout", url=url, timeout_sec=timeout_sec, attempt=attempt + 1)
                if attempt < _MAX_SCRAPE_RETRIES:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None
            except Exception as e:
                last_exc = e
                safe_log("crawl4ai_scrape_error", url=url, error=str(e), attempt=attempt + 1)
                if attempt < _MAX_SCRAPE_RETRIES:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None

            if not result.success:
                last_exc = Exception(result.error_message or "Unknown crawl4ai error")
                safe_log("crawl4ai_scrape_failed", url=url, error=result.error_message, attempt=attempt + 1)
                if attempt < _MAX_SCRAPE_RETRIES:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None

            if self._on_credits_used:
                await self._on_credits_used(1)

            md = result.markdown or ""
            return md if md else None

        return None