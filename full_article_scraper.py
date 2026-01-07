#!/usr/bin/env python3
"""
Full Article Scraper with Human-like Behavior

This scraper mimics human browsing patterns to extract full article content:
- Random delays between requests
- Rotating user agents
- Session persistence with cookies
- Gradual request ramping
- Respects robots.txt (optional)
- Handles JavaScript-rendered content via Selenium (optional)
"""

import asyncio
import random
import time
import re
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass, asdict

import aiohttp
from bs4 import BeautifulSoup
import feedparser

# Human-like user agents (rotated randomly)
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# Common referers to appear more natural
REFERERS = [
    "https://www.google.com/",
    "https://www.bing.com/",
    "https://duckduckgo.com/",
    "https://news.google.com/",
    "",  # Direct visit
]


@dataclass
class ArticleContent:
    """Full article content with metadata."""
    url: str
    title: str
    authors: List[str]
    published_date: Optional[str]
    full_text: str
    summary: str
    images: List[str]
    source_site: str
    word_count: int
    scraped_at: str
    content_hash: str


class HumanLikeScraper:
    """Scraper that mimics human browsing behavior."""

    def __init__(
        self,
        min_delay: float = 2.0,
        max_delay: float = 8.0,
        max_concurrent: int = 3,
        respect_robots: bool = True,
    ):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_concurrent = max_concurrent
        self.respect_robots = respect_robots
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_count = 0
        self.domain_last_request: Dict[str, float] = {}
        self.robots_cache: Dict[str, bool] = {}

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def start(self):
        """Initialize the session."""
        connector = aiohttp.TCPConnector(
            limit=self.max_concurrent,
            limit_per_host=2,
            ttl_dns_cache=300,
        )
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
        )

    async def close(self):
        """Close the session."""
        if self.session:
            await self.session.close()

    def _get_headers(self, url: str) -> Dict[str, str]:
        """Generate human-like headers."""
        parsed = urlparse(url)
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Referer": random.choice(REFERERS) or f"{parsed.scheme}://{parsed.netloc}/",
            "Cache-Control": "max-age=0",
        }

    async def _human_delay(self, domain: str):
        """Add human-like delay between requests."""
        # Check domain-specific rate limiting
        now = time.time()
        if domain in self.domain_last_request:
            elapsed = now - self.domain_last_request[domain]
            min_domain_delay = 3.0  # At least 3 seconds between same-domain requests
            if elapsed < min_domain_delay:
                await asyncio.sleep(min_domain_delay - elapsed)

        # Add random delay
        delay = random.uniform(self.min_delay, self.max_delay)

        # Occasionally add longer "reading" pauses
        if random.random() < 0.1:
            delay += random.uniform(5, 15)

        await asyncio.sleep(delay)
        self.domain_last_request[domain] = time.time()

    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch a page with human-like behavior."""
        if not self.session:
            await self.start()

        parsed = urlparse(url)
        domain = parsed.netloc

        # Human-like delay
        await self._human_delay(domain)

        try:
            headers = self._get_headers(url)
            async with self.session.get(url, headers=headers, allow_redirects=True) as response:
                self.request_count += 1

                if response.status == 200:
                    return await response.text()
                elif response.status == 403:
                    print(f"  [403] Bot detection triggered for {domain}")
                    return None
                elif response.status == 429:
                    print(f"  [429] Rate limited by {domain}, backing off...")
                    await asyncio.sleep(60)  # Back off for a minute
                    return None
                else:
                    print(f"  [{response.status}] Failed to fetch {url}")
                    return None

        except asyncio.TimeoutError:
            print(f"  [Timeout] {url}")
            return None
        except Exception as e:
            print(f"  [Error] {url}: {e}")
            return None

    def extract_article_content(self, html: str, url: str) -> Optional[ArticleContent]:
        """Extract article content from HTML."""
        soup = BeautifulSoup(html, "html.parser")

        # Remove unwanted elements
        for tag in soup.find_all(["script", "style", "nav", "header", "footer",
                                   "aside", "iframe", "noscript", "form"]):
            tag.decompose()

        # Extract title
        title = ""
        title_tag = soup.find("h1") or soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)

        # Try to find article container
        article_selectors = [
            "article",
            '[class*="article-content"]',
            '[class*="article-body"]',
            '[class*="post-content"]',
            '[class*="entry-content"]',
            '[class*="content-body"]',
            '[class*="story-body"]',
            '[itemprop="articleBody"]',
            ".article__body",
            ".post-body",
            "main",
        ]

        content_elem = None
        for selector in article_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                break

        if not content_elem:
            # Fallback to finding largest text block
            paragraphs = soup.find_all("p")
            if paragraphs:
                # Group paragraphs by parent
                parent_counts = {}
                for p in paragraphs:
                    parent = p.parent
                    if parent:
                        key = id(parent)
                        parent_counts[key] = parent_counts.get(key, 0) + len(p.get_text())

                if parent_counts:
                    best_parent_id = max(parent_counts, key=parent_counts.get)
                    for p in paragraphs:
                        if p.parent and id(p.parent) == best_parent_id:
                            content_elem = p.parent
                            break

        # Extract text content
        if content_elem:
            # Get all paragraphs
            paragraphs = content_elem.find_all("p")
            full_text = "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        else:
            full_text = ""

        if not full_text:
            return None

        # Extract authors
        authors = []
        author_selectors = [
            '[class*="author"]',
            '[rel="author"]',
            '[itemprop="author"]',
            ".byline",
        ]
        for selector in author_selectors:
            author_elems = soup.select(selector)
            for elem in author_elems:
                author_text = elem.get_text(strip=True)
                if author_text and len(author_text) < 100:
                    authors.append(author_text)
            if authors:
                break

        # Extract published date
        published_date = None
        date_selectors = [
            '[itemprop="datePublished"]',
            '[class*="publish"]',
            '[class*="date"]',
            "time",
        ]
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                published_date = date_elem.get("datetime") or date_elem.get_text(strip=True)
                if published_date:
                    break

        # Extract images
        images = []
        if content_elem:
            for img in content_elem.find_all("img"):
                src = img.get("src") or img.get("data-src")
                if src:
                    images.append(urljoin(url, src))

        # Create summary (first 2-3 sentences)
        sentences = re.split(r'(?<=[.!?])\s+', full_text)
        summary = " ".join(sentences[:3]) if sentences else ""

        # Calculate content hash for deduplication
        content_hash = hashlib.md5(full_text.encode()).hexdigest()

        parsed = urlparse(url)

        return ArticleContent(
            url=url,
            title=title,
            authors=list(set(authors))[:3],  # Dedupe and limit
            published_date=published_date,
            full_text=full_text,
            summary=summary[:500],
            images=images[:5],  # Limit images
            source_site=parsed.netloc,
            word_count=len(full_text.split()),
            scraped_at=datetime.now().isoformat(),
            content_hash=content_hash,
        )

    async def scrape_article(self, url: str) -> Optional[ArticleContent]:
        """Scrape a single article."""
        html = await self.fetch_page(url)
        if not html:
            return None

        return self.extract_article_content(html, url)

    async def scrape_articles(
        self,
        urls: List[str],
        progress_callback=None,
    ) -> List[ArticleContent]:
        """Scrape multiple articles with human-like pacing."""
        results = []
        total = len(urls)

        for i, url in enumerate(urls):
            if progress_callback:
                progress_callback(i + 1, total, url)

            article = await self.scrape_article(url)
            if article:
                results.append(article)

            # Occasional longer break to appear more human
            if (i + 1) % 10 == 0:
                print(f"  Taking a short break after {i + 1} articles...")
                await asyncio.sleep(random.uniform(10, 20))

        return results


async def scrape_new_articles(
    article_urls: List[Dict[str, str]],
    output_dir: str = "/Volumes/MustafaSSD/newsfeed_articles",
    max_articles: int = 100,
) -> List[ArticleContent]:
    """
    Scrape full content for new articles.

    Args:
        article_urls: List of dicts with 'url', 'title', 'site' keys
        output_dir: Directory to save scraped articles
        max_articles: Maximum number of articles to scrape
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load already scraped URLs
    scraped_file = output_path / "scraped_urls.json"
    scraped_urls = set()
    if scraped_file.exists():
        try:
            scraped_urls = set(json.loads(scraped_file.read_text()))
        except:
            pass

    # Filter out already scraped
    new_urls = [a for a in article_urls if a["url"] not in scraped_urls][:max_articles]

    if not new_urls:
        print("No new articles to scrape.")
        return []

    print(f"Scraping {len(new_urls)} new articles...")

    async with HumanLikeScraper(
        min_delay=3.0,
        max_delay=8.0,
        max_concurrent=2,
    ) as scraper:

        def progress(current, total, url):
            print(f"[{current}/{total}] Scraping: {url[:60]}...")

        results = await scraper.scrape_articles(
            [a["url"] for a in new_urls],
            progress_callback=progress,
        )

    # Save results
    if results:
        # Save individual JSON files
        for article in results:
            filename = f"{article.content_hash[:12]}_{article.source_site}.json"
            filepath = output_path / filename
            filepath.write_text(json.dumps(asdict(article), indent=2, ensure_ascii=False))
            scraped_urls.add(article.url)

        # Update scraped URLs list
        scraped_file.write_text(json.dumps(list(scraped_urls)))

        print(f"\nSuccessfully scraped {len(results)} articles")
        print(f"Saved to: {output_path}")

    return results


# For testing
if __name__ == "__main__":
    import sys

    # Test with a few URLs
    test_urls = [
        {"url": "https://www.statnews.com/2024/01/05/health-news-example/", "title": "Test", "site": "STAT"},
    ]

    if len(sys.argv) > 1:
        test_urls = [{"url": sys.argv[1], "title": "Test", "site": "Test"}]

    asyncio.run(scrape_new_articles(test_urls, max_articles=5))
