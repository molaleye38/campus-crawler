"""Scrapy settings for campus-crawler spiders.

These settings prioritize strict politeness over speed since we crawl
Nigerian government portals that may ban aggressive IPs.
"""

BOT_NAME = "campus-crawler"

SPIDER_MODULES = ["spiders"]
NEWSPIDER_MODULE = "spiders"

# ── Politeness (conservative) ──────────────────────────────────────────────
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1
# CONCURRENT_REQUESTS_PER_IP removed - conflicts with DownloaderAwarePriorityQueue
DOWNLOAD_DELAY = 10
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 10
AUTOTHROTTLE_MAX_DELAY = 30
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# ── Output (JSONLines: one JSON object per line) ───────────────────────────
FEED_FORMAT = "jsonlines"
FEED_EXPORT_ENCODING = "utf-8"
FEED_EXPORT_INDENT = None
FEED_STORE_EMPTY = False

# ── User-Agent rotation ────────────────────────────────────────────────────
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

# ── Request defaults ───────────────────────────────────────────────────────
ROBOTSTXT_OBEY = True
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Languages": "en-US,en;q=0.9",
}

# ── Disable cookies, caching, DNS caching (thin client) ────────────────────
COOKIES_ENABLED = False
TELNETCONSOLE_ENABLED = False
DNS_TIMEOUT = 10

# ── Extensions ─────────────────────────────────────────────────────────────
EXTENSIONS = {
    "scrapy.extensions.telnet.TelnetConsole": None,
}

# ── Logging ────────────────────────────────────────────────────────────────
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(levelname)s [spiders] %(message)s"