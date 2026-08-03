"""Test the crawler against a single institution to verify it works."""
import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from naija_admissions.crawl4ai_client import Crawl4AIClient
from naija_admissions.models import InstitutionSeed, InstitutionType, OwnershipType


async def test_simple_search():
    """Test DuckDuckGo search works."""
    print("=== Test 1: DuckDuckGo Search ===")
    async with Crawl4AIClient() as client:
        hits = await client.search("University of Lagos admission requirements", limit=3)
        print(f"Found {len(hits)} hits:")
        for h in hits:
            print(f"  - {h.title}: {h.url}")
    print("PASSED\n")


async def test_simple_scrape():
    """Test scraping a known working URL."""
    print("=== Test 2: Simple URL Scrape ===")
    async with Crawl4AIClient() as client:
        # Use a known reliable URL
        result = "None"
        for url in [
            "https://unilag.edu.ng",
            "https://www.jamb.gov.ng/",
        ]:
            try:
                md = await client.scrape(url)
                if md:
                    print(f"Scraped {url}: {len(md)} chars")
                    print(f"  Preview: {md[:200]}")
                    break
            except Exception as e:
                print(f"  Failed {url}: {e}")
        else:
            print("All URLs failed")
            return
    print("Test PASSED\n")


async def test_search_and_scrape():
    """Test full search + scrape pipeline."""
    print("=== Test 3: Search + Scrape Pipeline ===")
    async with Crawl4AIClient() as client:
        hits = await client.search(
            "Bayero University Kano admission requirements 2025",
            limit=3,
            scrape_contents=True
        )
        print(f"Search returned {len(hits)} hits")
        for h in hits:
            print(f"  {h.title}")
            if h.content:
                print(f"    Content: {len(h.content)} chars")
            else:
                print(f"    No content (likely timeout or dead URL)")
    print("Test 3 DONE\n")


async def test_with_timeout():
    """Test scraping with explicit timeout."""
    print("=== Test 4: Scrape with timeout handling ===")
    async with Crawl4AIClient() as client:
        problem_urls = [
            "https://www.buk.edu.ng/police",  # Known timeout
            "https://unilag.edu.ng",
        ]
        for url in problem_urls:
            try:
                task = asyncio.wait_for(
                    client.scrape(url),
                    timeout=20.0  # 20s timeout
                )
                result = await task
                if result:
                    print(f"  {url}: SUCCESS ({len(result)} chars)")
                else:
                    print(f"  {url}: No content returned")
            except asyncio.TimeoutError:
                print(f"  {url}: TIMEOUT after 20s (skipped)")
            except Exception as e:
                print(f"  {url}: ERROR {e}")
    print("Test 4 DONE\n")


if __name__ == "__main__":
    asyncio.run(test_simple_search())
    asyncio.run(asyncio.to_thread(lambda: None) or test_search_and_scrape())