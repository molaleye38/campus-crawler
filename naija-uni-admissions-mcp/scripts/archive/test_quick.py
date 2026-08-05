"""Quick test - verify DuckDuckGo search + Crawl4AI scraping work."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "naija-uni-admissions-mcp", "src"))

from naija_admissions.crawl4ai_client import Crawl4AIClient


async def main():
    print("=== Testing Search + Scrape ===")
    async with Crawl4AIClient() as client:
        hits = await client.search(
            "Bayero University Kano admission requirements 2025",
            limit=3,
            scrape_contents=True
        )
        print(f"Found {len(hits)} hits:")
        for h in hits:
            print(f"  {h.title}")
            if h.content:
                print(f"    Content: {len(h.content)} chars")
                print(f"    Preview: {h.content[:300]}")
            else:
                print(f"    No content (URL likely dead or timed out from GH Actions)")
    print("Done")


if __name__ == "__main__":
    asyncio.run(main())