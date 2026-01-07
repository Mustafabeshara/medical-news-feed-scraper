#!/usr/bin/env python3
"""
Selenium-based Full Article Scraper

Uses Selenium with undetected-chromedriver to bypass bot detection.
Mimics human behavior with:
- Mouse movements
- Scrolling patterns
- Random delays
- Realistic viewport sizes
"""

import asyncio
import json
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
import hashlib
import re

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Selenium not installed. Install with: pip3 install selenium")

try:
    import undetected_chromedriver as uc
    UC_AVAILABLE = True
except ImportError:
    UC_AVAILABLE = False


@dataclass
class ScrapedArticle:
    """Scraped article data."""
    url: str
    title: str
    full_text: str
    authors: List[str]
    published_date: Optional[str]
    images: List[str]
    word_count: int
    scraped_at: str
    source_domain: str
    content_hash: str


class SeleniumScraper:
    """Human-like web scraper using Selenium."""

    VIEWPORT_SIZES = [
        (1920, 1080),
        (1440, 900),
        (1366, 768),
        (1536, 864),
        (1280, 720),
    ]

    def __init__(
        self,
        headless: bool = True,
        use_undetected: bool = True,
        min_delay: float = 3.0,
        max_delay: float = 8.0,
    ):
        self.headless = headless
        self.use_undetected = use_undetected and UC_AVAILABLE
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.driver: Optional[webdriver.Chrome] = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.close()

    def start(self):
        """Initialize the browser."""
        viewport = random.choice(self.VIEWPORT_SIZES)

        if self.use_undetected:
            options = uc.ChromeOptions()
            if self.headless:
                options.add_argument("--headless=new")
            options.add_argument(f"--window-size={viewport[0]},{viewport[1]}")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")

            self.driver = uc.Chrome(options=options)
        else:
            options = Options()
            if self.headless:
                options.add_argument("--headless=new")
            options.add_argument(f"--window-size={viewport[0]},{viewport[1]}")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            self.driver = webdriver.Chrome(options=options)

            # Mask webdriver property
            self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """}
            )

        self.driver.set_page_load_timeout(30)

    def close(self):
        """Close the browser."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

    def _human_delay(self):
        """Add human-like random delay."""
        time.sleep(random.uniform(self.min_delay, self.max_delay))

    def _simulate_reading(self):
        """Simulate human reading behavior with scrolling."""
        if not self.driver:
            return

        try:
            # Get page height
            page_height = self.driver.execute_script("return document.body.scrollHeight")
            viewport_height = self.driver.execute_script("return window.innerHeight")

            # Scroll down gradually like reading
            current_pos = 0
            while current_pos < page_height - viewport_height:
                # Random scroll amount (like reading)
                scroll_amount = random.randint(100, 400)
                current_pos += scroll_amount

                self.driver.execute_script(f"window.scrollTo(0, {current_pos});")

                # Reading pause
                time.sleep(random.uniform(0.5, 2.0))

                # Occasionally pause longer (like reading a paragraph)
                if random.random() < 0.2:
                    time.sleep(random.uniform(2, 5))

            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)

        except Exception:
            pass

    def _move_mouse_randomly(self):
        """Simulate random mouse movements."""
        if not self.driver:
            return

        try:
            actions = ActionChains(self.driver)

            # Find some elements to hover over
            elements = self.driver.find_elements(By.TAG_NAME, "a")[:5]
            elements += self.driver.find_elements(By.TAG_NAME, "p")[:3]

            if elements:
                for _ in range(random.randint(2, 5)):
                    elem = random.choice(elements)
                    try:
                        actions.move_to_element(elem).perform()
                        time.sleep(random.uniform(0.3, 1.0))
                    except:
                        pass
        except Exception:
            pass

    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch a page with human-like behavior."""
        if not self.driver:
            self.start()

        try:
            # Navigate to page
            self.driver.get(url)

            # Wait for page to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Human-like behavior
            self._human_delay()
            self._move_mouse_randomly()

            # Light scrolling
            if random.random() < 0.5:
                self._simulate_reading()

            return self.driver.page_source

        except TimeoutException:
            print(f"  [Timeout] {url}")
            return None
        except WebDriverException as e:
            print(f"  [WebDriver Error] {url}: {e}")
            return None
        except Exception as e:
            print(f"  [Error] {url}: {e}")
            return None

    def extract_content(self, url: str) -> Optional[ScrapedArticle]:
        """Extract article content from current page."""
        if not self.driver:
            return None

        try:
            from bs4 import BeautifulSoup
            from urllib.parse import urlparse

            html = self.driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            # Remove unwanted elements
            for tag in soup.find_all(["script", "style", "nav", "header", "footer",
                                       "aside", "iframe", "noscript", "form", "ad"]):
                tag.decompose()

            # Extract title
            title = ""
            title_elem = soup.find("h1") or soup.find("title")
            if title_elem:
                title = title_elem.get_text(strip=True)

            # Find article content
            article_selectors = [
                "article",
                '[class*="article-content"]',
                '[class*="article-body"]',
                '[class*="post-content"]',
                '[class*="entry-content"]',
                '[class*="story-body"]',
                '[itemprop="articleBody"]',
                "main",
            ]

            content_elem = None
            for selector in article_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    break

            # Extract paragraphs
            if content_elem:
                paragraphs = content_elem.find_all("p")
            else:
                paragraphs = soup.find_all("p")

            full_text = "\n\n".join(
                p.get_text(strip=True)
                for p in paragraphs
                if p.get_text(strip=True) and len(p.get_text(strip=True)) > 50
            )

            if not full_text or len(full_text) < 200:
                return None

            # Extract authors
            authors = []
            author_selectors = ['[class*="author"]', '[rel="author"]', ".byline"]
            for selector in author_selectors:
                for elem in soup.select(selector)[:3]:
                    text = elem.get_text(strip=True)
                    if text and len(text) < 100:
                        authors.append(text)
                if authors:
                    break

            # Extract date
            published_date = None
            date_selectors = ['[datetime]', '[class*="date"]', 'time']
            for selector in date_selectors:
                elem = soup.select_one(selector)
                if elem:
                    published_date = elem.get("datetime") or elem.get_text(strip=True)
                    if published_date:
                        break

            # Extract images
            images = []
            if content_elem:
                for img in content_elem.find_all("img")[:5]:
                    src = img.get("src") or img.get("data-src")
                    if src and not src.startswith("data:"):
                        images.append(src)

            parsed = urlparse(url)
            content_hash = hashlib.md5(full_text.encode()).hexdigest()

            return ScrapedArticle(
                url=url,
                title=title,
                full_text=full_text,
                authors=list(set(authors))[:3],
                published_date=published_date,
                images=images,
                word_count=len(full_text.split()),
                scraped_at=datetime.now().isoformat(),
                source_domain=parsed.netloc,
                content_hash=content_hash,
            )

        except Exception as e:
            print(f"  [Extract Error] {url}: {e}")
            return None

    def scrape_article(self, url: str) -> Optional[ScrapedArticle]:
        """Scrape a single article."""
        html = self.fetch_page(url)
        if not html:
            return None
        return self.extract_content(url)


def scrape_articles_selenium(
    urls: List[str],
    output_dir: str = "/Volumes/MustafaSSD/newsfeed_articles",
    headless: bool = True,
    max_articles: int = 50,
) -> List[ScrapedArticle]:
    """
    Scrape articles using Selenium.

    Args:
        urls: List of article URLs to scrape
        output_dir: Directory to save results
        headless: Run browser in headless mode
        max_articles: Maximum articles to scrape
    """
    if not SELENIUM_AVAILABLE:
        print("Selenium not available. Install with: pip3 install selenium")
        return []

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load already scraped
    scraped_file = output_path / "selenium_scraped.json"
    scraped_urls = set()
    if scraped_file.exists():
        try:
            scraped_urls = set(json.loads(scraped_file.read_text()))
        except:
            pass

    # Filter
    new_urls = [u for u in urls if u not in scraped_urls][:max_articles]

    if not new_urls:
        print("No new articles to scrape.")
        return []

    print(f"Scraping {len(new_urls)} articles with Selenium...")
    results = []

    with SeleniumScraper(headless=headless, min_delay=4.0, max_delay=10.0) as scraper:
        for i, url in enumerate(new_urls):
            print(f"[{i+1}/{len(new_urls)}] {url[:60]}...")

            article = scraper.scrape_article(url)
            if article:
                results.append(article)

                # Save individual file
                filename = f"selenium_{article.content_hash[:12]}_{article.source_domain}.json"
                filepath = output_path / filename
                filepath.write_text(json.dumps(asdict(article), indent=2, ensure_ascii=False))

                scraped_urls.add(url)
                print(f"  -> Scraped {article.word_count} words")
            else:
                print(f"  -> Failed to extract content")

            # Occasional longer break
            if (i + 1) % 5 == 0:
                print("  Taking a break...")
                time.sleep(random.uniform(15, 30))

    # Save scraped URLs
    scraped_file.write_text(json.dumps(list(scraped_urls)))

    print(f"\nScraped {len(results)} articles successfully")
    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python selenium_scraper.py <url> [url2] [url3] ...")
        print("\nExample:")
        print("  python selenium_scraper.py https://www.statnews.com/article/...")
        sys.exit(1)

    urls = sys.argv[1:]
    results = scrape_articles_selenium(urls, headless=False, max_articles=10)

    for article in results:
        print(f"\n{'='*60}")
        print(f"Title: {article.title}")
        print(f"Words: {article.word_count}")
        print(f"Authors: {', '.join(article.authors)}")
        print(f"Preview: {article.full_text[:200]}...")
