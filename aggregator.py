import asyncio
import logging
import random
import time
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
import feedparser
from dateutil import parser as dateparser

from config import CONFIG
from security import validate_url
from entity_extractor import enrich_article

# Playwright for browser automation (handles bot detection)
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Rotate User-Agents to avoid detection
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

def _get_headers(for_feed: bool = False) -> Dict[str, str]:
    """Get headers with rotating User-Agent."""
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",  # Don't request Brotli (br) - requests can't decode it
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }
    if for_feed:
        headers["Accept"] = "application/rss+xml, application/atom+xml, application/xml, text/xml, */*"
    else:
        headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    return headers

TIMEOUT = CONFIG.timeout_seconds
MAX_RETRIES = CONFIG.max_retries
RETRY_DELAY = CONFIG.retry_delay_seconds

logger = logging.getLogger(__name__)

Feed = Dict[str, Any]
Article = Dict[str, Any]

FEED_TYPES = {
    "application/rss+xml",
    "application/atom+xml",
    "application/xml",
    "text/xml",
    "application/json",
    "application/feed+json",
}

# Extended common feed paths
COMMON_FEED_PATHS = [
    "/feed",
    "/feed/",
    "/feeds",
    "/rss",
    "/rss/",
    "/rss.xml",
    "/atom.xml",
    "/index.xml",
    "/feed.xml",
    "/news/feed",
    "/news/rss",
    "/blog/feed",
    "/latest/rss",
    "/?feed=rss2",
    "/rss/news",
    "/rss/all",
]


def _safe_get(url: str, for_feed: bool = False, retries: int = MAX_RETRIES) -> Optional[requests.Response]:
    """Make HTTP request with retry logic and rotating headers."""
    # Validate URL to prevent SSRF attacks
    if not validate_url(url):
        logger.error(f"URL failed security validation: {url}")
        return None

    for attempt in range(retries + 1):
        try:
            headers = _get_headers(for_feed=for_feed)
            resp = requests.get(
                url,
                headers=headers,
                timeout=TIMEOUT,
                allow_redirects=True,
                verify=True
            )
            if resp.status_code == 200:
                return resp
            elif resp.status_code == 403:
                # Bot detection - try with different headers on retry
                if attempt < retries:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                logger.warning("403 Forbidden for %s (bot detection likely)", url)
            elif resp.status_code == 429:
                # Rate limited
                if attempt < retries:
                    time.sleep(RETRY_DELAY * 2 * (attempt + 1))
                    continue
                logger.warning("429 Rate Limited for %s", url)
            elif resp.status_code >= 500:
                # Server error - retry
                if attempt < retries:
                    time.sleep(RETRY_DELAY)
                    continue
                logger.warning("Server error %s for %s", resp.status_code, url)
            else:
                logger.warning("Non-200 status for %s: %s", url, resp.status_code)
        except requests.exceptions.Timeout:
            if attempt < retries:
                time.sleep(RETRY_DELAY)
                continue
            logger.warning("Timeout for %s", url)
        except requests.exceptions.SSLError as e:
            logger.warning("SSL error for %s: %s", url, e)
            break  # Don't retry SSL errors
        except requests.RequestException as e:
            if attempt < retries:
                time.sleep(RETRY_DELAY)
                continue
            logger.warning("Request failed for %s: %s", url, e)
    return None


def discover_feeds(homepage_url: str) -> List[str]:
    """Discover feed URLs from a homepage by inspecting <link rel="alternate">.

    Falls back to common feed path guesses.
    """
    feeds: List[str] = []
    resp = _safe_get(homepage_url)
    if resp is not None:
        soup = BeautifulSoup(resp.text, "html.parser")

        # Method 1: Look for <link rel="alternate"> tags
        for link in soup.find_all("link", attrs={"rel": "alternate"}):
            href = link.get("href")
            type_ = (link.get("type") or "").strip().lower()
            if not href:
                continue
            if type_ in FEED_TYPES or "rss" in type_ or "atom" in type_ or "feed" in type_:
                feeds.append(urljoin(homepage_url, href))

        # Method 2: Look for links to RSS/Atom in meta tags
        for meta in soup.find_all("meta", attrs={"property": "og:see_also"}):
            content = meta.get("content", "")
            if "rss" in content.lower() or "feed" in content.lower():
                feeds.append(content)

        # Method 3: Find anchors with RSS mentions
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = (a.get_text() or "").lower()
            href_lower = href.lower()
            if any(kw in href_lower for kw in ["rss", "feed", "atom", ".xml"]) or "rss" in text:
                feeds.append(urljoin(homepage_url, href))

        # Method 4: Look for RSS icons/images
        for img in soup.find_all("img"):
            parent = img.find_parent("a")
            if parent and parent.get("href"):
                alt = (img.get("alt") or "").lower()
                src = (img.get("src") or "").lower()
                if "rss" in alt or "feed" in alt or "rss" in src:
                    feeds.append(urljoin(homepage_url, parent["href"]))

    # Fallback to common paths - only test a few to avoid slowdowns
    parsed = urlparse(homepage_url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    # Only check common paths if we haven't found any feeds
    if not feeds:
        for p in COMMON_FEED_PATHS[:8]:  # Limit to avoid too many requests
            candidate = urljoin(base, p)
            r = _safe_get(candidate, for_feed=True, retries=0)  # Quick check, no retries
            if r is not None:
                ct = (r.headers.get("Content-Type") or "").lower()
                content_start = r.text.strip()[:100].lower()
                if (
                    any(t in ct for t in ["xml", "rss", "atom", "json"])
                    or content_start.startswith("<?xml")
                    or content_start.startswith("<rss")
                    or content_start.startswith("<feed")
                    or content_start.startswith("{")
                ):
                    feeds.append(candidate)

    # De-duplicate while preserving order
    seen = set()
    unique = []
    for f in feeds:
        normalized = f.rstrip("/").lower()
        if normalized not in seen:
            unique.append(f)
            seen.add(normalized)
    return unique


def parse_feed(feed_url: str) -> Tuple[List[Article], Optional[str]]:
    """Parse a feed URL and return normalized articles and an optional source name."""
    # feedparser handles its own HTTP requests, but we can pass content directly
    resp = _safe_get(feed_url, for_feed=True)
    if resp is None:
        return [], None

    # Use resp.text (decoded) instead of resp.content (raw bytes)
    # This ensures gzip/deflate responses are properly decoded
    # Parse with safe settings to prevent XXE attacks
    parsed = feedparser.parse(resp.text)
    feedparser.SANITIZE_HTML = True
    source_title: Optional[str] = None
    if hasattr(parsed, "feed"):
        source_title = parsed.feed.get("title") or parsed.feed.get("link")

    articles: List[Article] = []
    for e in parsed.entries:
        title = e.get("title") or "Untitled"
        link = e.get("link") or ""
        summary = e.get("summary") or e.get("description") or ""

        # Clean up summary (remove HTML tags if present)
        if summary:
            summary_soup = BeautifulSoup(summary, "html.parser")
            summary = summary_soup.get_text(separator=" ", strip=True)[:500]

        published: Optional[str] = None
        for key in ("published", "updated", "created", "pubDate"):
            val = e.get(key)
            if val:
                try:
                    dt = dateparser.parse(val, fuzzy=True)
                    if dt:
                        published = dt.isoformat()
                        break
                except Exception:
                    pass

        # Extract image from various sources
        image: Optional[str] = None
        media = e.get("media_content") or e.get("media_thumbnail")
        if media and isinstance(media, list) and media:
            image = media[0].get("url")
        elif e.get("image") and isinstance(e.get("image"), dict):
            image = e.get("image").get("href") or e.get("image").get("url")

        # Try to extract image from content/summary
        if not image and summary:
            img_match = BeautifulSoup(e.get("summary") or "", "html.parser").find("img")
            if img_match and img_match.get("src"):
                image = img_match.get("src")

        # Try enclosures
        if not image:
            enclosures = e.get("enclosures") or []
            for enc in enclosures:
                if enc.get("type", "").startswith("image/"):
                    image = enc.get("href") or enc.get("url")
                    break

        articles.append(
            {
                "title": title,
                "link": link,
                "summary": summary,
                "published": published,
                "image": image,
                "source": source_title,
                "feed": feed_url,
            }
        )
    return articles, source_title


def scrape_homepage_articles(homepage_url: str, limit: int = 50) -> List[Article]:
    """Lightweight homepage scraping to extract headlines when feeds are absent.

    Heuristics only: prefer <article> blocks, otherwise pick anchors in likely content areas.
    """
    resp = _safe_get(homepage_url)
    if resp is None:
        return []
    soup = BeautifulSoup(resp.text, "html.parser")

    def normalize_link(href: Optional[str]) -> Optional[str]:
        if not href:
            return None
        return urljoin(homepage_url, href)

    articles: List[Article] = []
    seen = set()

    # Strategy 1: explicit <article> elements
    for art in soup.find_all("article"):
        a = art.find("a", href=True)
        title = None
        if a:
            title = (a.get_text() or "").strip()
        if not title:
            h = art.find(["h1", "h2", "h3", "h4"]) or art.find(class_=lambda c: c and "title" in str(c).lower())
            if h:
                title = (h.get_text() or "").strip()
        link = normalize_link(a["href"]) if a and a.get("href") else None
        if not title or not link or len(title) < 10:
            continue
        if link in seen:
            continue
        # summary
        p = art.find("p")
        summary = p.get_text().strip()[:300] if p else ""
        # image
        img = art.find("img")
        image = normalize_link(img.get("src") or img.get("data-src")) if img else None
        # published
        t = art.find("time")
        published = None
        if t and (t.get("datetime") or t.get_text()):
            val = t.get("datetime") or t.get_text()
            try:
                dt = dateparser.parse(val, fuzzy=True)
                if dt:
                    published = dt.isoformat()
            except Exception:
                published = None
        articles.append(
            {
                "title": title,
                "link": link,
                "summary": summary,
                "published": published,
                "image": image,
                "source": urlparse(homepage_url).netloc,
                "feed": None,
            }
        )
        seen.add(link)
        if len(articles) >= limit:
            return articles

    if len(articles) >= 5:
        return articles

    # Strategy 2: Look for common news item patterns
    news_selectors = [
        {"class_": lambda x: x and any(kw in str(x).lower() for kw in ["article", "news", "story", "post", "item", "card"])},
        {"role": "article"},
    ]

    for selector in news_selectors:
        for el in soup.find_all(["div", "li", "section"], **selector):
            a = el.find("a", href=True)
            if not a:
                continue
            title = None
            h = el.find(["h1", "h2", "h3", "h4", "h5"])
            if h:
                title = h.get_text().strip()
            if not title:
                title = a.get_text().strip()
            if not title or len(title) < 15 or len(title) > 200:
                continue
            link = normalize_link(a["href"])
            if not link or link in seen:
                continue
            # Skip navigation/menu links
            if any(kw in link.lower() for kw in ["/tag/", "/category/", "/author/", "/page/", "javascript:", "#"]):
                continue

            p = el.find("p")
            summary = p.get_text().strip()[:300] if p else ""
            img = el.find("img")
            image = normalize_link(img.get("src") or img.get("data-src")) if img else None

            articles.append({
                "title": title,
                "link": link,
                "summary": summary,
                "published": None,
                "image": image,
                "source": urlparse(homepage_url).netloc,
                "feed": None,
            })
            seen.add(link)
            if len(articles) >= limit:
                return articles

    # Strategy 3: anchors from likely content containers
    containers = []
    for el in soup.find_all(["section", "div", "main", "ul"]):
        cls = " ".join(el.get("class") or [])
        ident = el.get("id") or ""
        label = f"{cls} {ident}".lower()
        if any(k in label for k in ["content", "main", "article", "news", "story", "feed", "list", "posts"]):
            containers.append(el)
    if not containers:
        containers = [soup.body] if soup.body else [soup]

    def is_noise(label: str) -> bool:
        return any(k in label for k in ["nav", "menu", "footer", "subscribe", "login", "cookie", "sidebar", "widget"])

    for cont in containers:
        for a in cont.find_all("a", href=True):
            href = a["href"]
            text = (a.get_text() or "").strip()
            if not text or len(text) < 25 or len(text) > 180:
                continue
            parent = a.parent
            label = " ".join((parent.get("class") or [])) if parent else ""
            if is_noise(label.lower()):
                continue
            link = normalize_link(href)
            if not link or link in seen:
                continue
            # Skip common non-article links
            if any(kw in link.lower() for kw in ["/tag/", "/category/", "/author/", "javascript:", "#", "mailto:", "tel:"]):
                continue
            summary = ""
            p = parent.find("p") if parent else None
            if p:
                summary = (p.get_text() or "").strip()[:300]
            articles.append(
                {
                    "title": text,
                    "link": link,
                    "summary": summary,
                    "published": None,
                    "image": None,
                    "source": urlparse(homepage_url).netloc,
                    "feed": None,
                }
            )
            seen.add(link)
            if len(articles) >= limit:
                return articles
    return articles


# ============================================================================
# BROWSER-BASED SCRAPING (for sites with bot detection)
# ============================================================================

# Sites that require browser automation due to bot detection or JS rendering
BROWSER_REQUIRED_SITES = {
    "medscape.com": True,
    "auntminnie.com": True,
    "jvir.org": True,
    "jvascsurg.org": True,
    "gastrojournal.org": True,
    "anesthesiologynews.com": True,
    "painmedicinenews.com": True,
    "gastroendonews.com": True,
    "clinicaloncology.com": True,
    "intuitive.com": True,
    "journals.lww.com": True,
}


def _needs_browser(url: str) -> bool:
    """Check if a URL requires browser automation."""
    if not url:
        return False
    parsed = urlparse(url)
    domain = parsed.netloc.lower().replace("www.", "")
    return any(site in domain for site in BROWSER_REQUIRED_SITES)


async def _browser_get_page_content(url: str, wait_selector: Optional[str] = None) -> Optional[str]:
    """Fetch page content using a headless browser."""
    if not PLAYWRIGHT_AVAILABLE:
        logger.warning("Playwright not available for browser-based scraping")
        return None

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 1920, "height": 1080},
            )
            page = await context.new_page()

            # Block unnecessary resources for speed
            await page.route("**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2}", lambda route: route.abort())

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)

                # Wait for content to load
                if wait_selector:
                    try:
                        await page.wait_for_selector(wait_selector, timeout=5000)
                    except Exception:
                        pass  # Continue even if selector not found

                # Small delay for JS to render
                await asyncio.sleep(1)

                content = await page.content()
                return content
            finally:
                await browser.close()
    except Exception as e:
        logger.warning("Browser fetch failed for %s: %s", url, e)
        return None


async def browser_fetch_feed(feed_url: str) -> Tuple[List[Article], Optional[str]]:
    """Fetch and parse a feed using browser automation."""
    content = await _browser_get_page_content(feed_url)
    if not content:
        return [], None

    # Parse the feed content
    parsed = feedparser.parse(content)
    source_title: Optional[str] = None
    if hasattr(parsed, "feed") and parsed.feed:
        feed_data = parsed.feed  # type: ignore[assignment]
        source_title = str(feed_data.get("title", "")) or str(feed_data.get("link", "")) or None  # type: ignore[union-attr]

    articles: List[Article] = []
    for e in parsed.entries:
        title = str(e.get("title", "")) or "Untitled"
        link = str(e.get("link", ""))
        summary_raw = e.get("summary") or e.get("description") or ""
        summary = str(summary_raw) if summary_raw else ""

        if summary:
            summary_soup = BeautifulSoup(summary, "html.parser")
            summary = summary_soup.get_text(separator=" ", strip=True)[:500]

        published: Optional[str] = None
        for key in ("published", "updated", "created", "pubDate"):
            val = e.get(key)
            if val:
                try:
                    dt = dateparser.parse(str(val), fuzzy=True)
                    if dt:
                        published = dt.isoformat()
                        break
                except Exception:
                    pass

        image: Optional[str] = None
        media = e.get("media_content") or e.get("media_thumbnail")
        if media and isinstance(media, list) and len(media) > 0:
            image = str(media[0].get("url", "")) or None

        articles.append({
            "title": title,
            "link": link,
            "summary": summary,
            "published": published,
            "image": image,
            "source": source_title,
            "feed": feed_url,
        })

    return articles, source_title


async def browser_scrape_homepage(homepage_url: str, limit: int = 50) -> List[Article]:
    """Scrape a homepage using browser automation for JS-heavy sites."""
    content = await _browser_get_page_content(
        homepage_url,
        wait_selector="article, .article, .news-item, .story, .press-release, .card"
    )
    if not content:
        return []

    soup = BeautifulSoup(content, "html.parser")
    articles: List[Article] = []
    seen = set()

    def normalize_link(href: Optional[str]) -> Optional[str]:
        if not href:
            return None
        return urljoin(homepage_url, href)

    # Strategy 1: Look for article elements with various class patterns
    article_patterns = ["article", "news", "story", "post", "item", "card", "teaser", "press", "release", "entry"]
    for art in soup.find_all(["article", "div", "li", "section"], class_=lambda c: c and any(
        kw in str(c).lower() for kw in article_patterns
    )):
        a = art.find("a", href=True)
        if not a:
            continue

        title = None
        h = art.find(["h1", "h2", "h3", "h4", "h5", "h6"])
        if h:
            title = h.get_text().strip()
        if not title:
            # Try getting title from link text
            title = a.get_text().strip()
        if not title:
            # Try title attribute
            title = a.get("title", "").strip()

        if not title or len(title) < 10:
            continue

        link = normalize_link(a["href"])
        if not link or link in seen:
            continue

        # Skip navigation links
        skip_patterns = ["/tag/", "/category/", "/author/", "javascript:", "#", "mailto:", "tel:", "/search", "/login"]
        if any(kw in link.lower() for kw in skip_patterns):
            continue

        p = art.find("p")
        summary = p.get_text().strip()[:300] if p else ""

        img = art.find("img")
        image = normalize_link(img.get("src") or img.get("data-src") or img.get("data-lazy-src")) if img else None

        t = art.find("time")
        published = None
        if t and (t.get("datetime") or t.get_text()):
            val = t.get("datetime") or t.get_text()
            try:
                dt = dateparser.parse(str(val), fuzzy=True)
                if dt:
                    published = dt.isoformat()
            except Exception:
                pass

        articles.append({
            "title": title,
            "link": link,
            "summary": summary,
            "published": published,
            "image": image,
            "source": urlparse(homepage_url).netloc,
            "feed": None,
        })
        seen.add(link)

        if len(articles) >= limit:
            return articles

    # Strategy 2: If no articles found, look for links that appear to be news articles
    if not articles:
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            text = a.get_text().strip()

            # Must have meaningful text
            if len(text) < 20 or len(text) > 300:
                continue

            link = normalize_link(href)
            if not link or link in seen:
                continue

            # Look for article-like URLs
            article_url_patterns = ["/news/", "/press/", "/article/", "/release/", "/blog/", "2024", "2025"]
            if not any(p in link.lower() for p in article_url_patterns):
                continue

            # Skip navigation
            skip_patterns = ["/tag/", "/category/", "/author/", "javascript:", "#", "/page/"]
            if any(kw in link.lower() for kw in skip_patterns):
                continue

            articles.append({
                "title": text,
                "link": link,
                "summary": "",
                "published": None,
                "image": None,
                "source": urlparse(homepage_url).netloc,
                "feed": None,
            })
            seen.add(link)

            if len(articles) >= limit:
                break

    return articles


async def fetch_site_articles(site: Dict[str, Any]) -> Tuple[str, List[Article]]:
    """Fetch articles for a single site definition.

    Site dict keys: name (optional), url (optional), feeds (optional list)
    Returns: (site_name, articles)
    """
    name = site.get("name")
    url = site.get("url")
    explicit_feeds = site.get("feeds") or []

    feeds: List[str] = []
    if explicit_feeds:
        feeds.extend(explicit_feeds)
    if url:
        discovered = discover_feeds(url)
        feeds.extend(discovered)

    # Use domain as fallback name
    if not name:
        if url:
            name = urlparse(url).netloc
        elif explicit_feeds:
            name = urlparse(explicit_feeds[0]).netloc
        else:
            name = "Unknown Source"

    # Aggregate articles across feeds
    articles: List[Article] = []
    seen_links = set()

    for f in feeds:
        try:
            # Try regular HTTP first
            items, source_title = parse_feed(f)

            # If no items and site needs browser, try browser-based fetch
            if not items and _needs_browser(f) and PLAYWRIGHT_AVAILABLE:
                logger.info("Trying browser fetch for %s", f)
                items, source_title = await browser_fetch_feed(f)

            for it in items:
                link = it.get("link")
                if link and link not in seen_links:
                    it["site"] = name
                    if source_title:
                        it["source"] = source_title
                    articles.append(it)
                    seen_links.add(link)
        except Exception as e:
            logger.warning("Failed parsing feed %s: %s", f, e)
            continue

    # Fallback: scrape homepage when feeds are missing or produced no items
    if not articles and url:
        try:
            # Try regular scraping first
            scraped = scrape_homepage_articles(url)

            # If no articles and site needs browser, try browser-based scraping
            if not scraped and _needs_browser(url) and PLAYWRIGHT_AVAILABLE:
                logger.info("Trying browser scrape for %s", url)
                scraped = await browser_scrape_homepage(url)

            for it in scraped:
                link = it.get("link")
                if link and link not in seen_links:
                    it["site"] = name
                    articles.append(it)
                    seen_links.add(link)
        except Exception as e:
            logger.warning("Failed scraping homepage %s: %s", url, e)

    # Enrich articles with extracted companies and products
    articles = [enrich_article(article) for article in articles]

    return name, articles


async def fetch_all_sites(sites: List[Dict[str, Any]]) -> Dict[str, List[Article]]:
    """Fetch articles from all sites with controlled concurrency."""
    results: Dict[str, List[Article]] = {}

    # Use semaphore for rate limiting - concurrent requests
    semaphore = asyncio.Semaphore(CONFIG.concurrent_requests)

    async def fetch_with_limit(site: Dict[str, Any]) -> Tuple[str, List[Article]]:
        async with semaphore:
            try:
                name, articles = await fetch_site_articles(site)
                await asyncio.sleep(0.1)  # Small delay between requests
                return name, articles
            except Exception as e:
                site_name = site.get('name', site.get('url', 'unknown'))
                logger.error(f"Error fetching {site_name}: {e}")
                return site.get('name', site.get('url', 'unknown')), []

    # Fetch concurrently
    logger.info(f"Fetching {len(sites)} sites with max {CONFIG.concurrent_requests} concurrent requests")
    tasks = [fetch_with_limit(site) for site in sites]
    site_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    for result in site_results:
        if isinstance(result, Exception):
            logger.error(f"Site fetch failed with exception: {result}")
            continue
        name, articles = result
        if articles:  # Only add if we got articles
            results[name] = articles

    logger.info(f"Fetched articles from {len(results)} sites successfully")
    return results


def filter_articles(
    articles: List[Article], site: Optional[str] = None, q: Optional[str] = None, limit: int = 50
) -> List[Article]:
    filtered = []
    ql = (q or "").lower().strip()
    for a in articles:
        if site and a.get("site") != site:
            continue
        if ql:
            hay = " ".join(
                [
                    a.get("title") or "",
                    a.get("summary") or "",
                    a.get("source") or "",
                ]
            ).lower()
            if ql not in hay:
                continue
        filtered.append(a)
        if len(filtered) >= limit:
            break
    return filtered
