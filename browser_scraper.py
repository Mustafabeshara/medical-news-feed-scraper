"""
Browser-based scraper for sites that block direct RSS/HTTP access.
Uses Playwright to bypass anti-scraping measures.
"""

import asyncio
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BrowserScraper:
    """Scrapes news articles using browser automation"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.playwright = None
        
    async def __aenter__(self):
        """Context manager entry"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def scrape_site(self, url: str, selectors: Dict[str, str]) -> List[Dict]:
        """
        Scrape a site using CSS selectors
        
        Args:
            url: The URL to scrape
            selectors: Dict with keys: 'article', 'title', 'link', 'date' (optional)
            
        Returns:
            List of article dictionaries
        """
        if not self.browser:
            raise RuntimeError("Browser not initialized. Use 'async with BrowserScraper()' context manager.")
        
        page = await self.browser.new_page()
        articles = []
        
        try:
            # Navigate to the page
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for articles to load
            await page.wait_for_selector(selectors['article'], timeout=10000)
            
            # Get page content
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find all article elements
            article_elements = soup.select(selectors['article'])
            
            for element in article_elements:
                try:
                    # Extract title
                    title_elem = element.select_one(selectors['title'])
                    title = title_elem.get_text(strip=True) if title_elem else None
                    
                    # Extract link
                    link_elem = element.select_one(selectors['link'])
                    if link_elem:
                        link = link_elem.get('href', '')
                        # Handle relative URLs
                        if link and not link.startswith('http'):
                            from urllib.parse import urljoin
                            link = urljoin(url, link)
                    else:
                        link = None
                    
                    # Extract date if selector provided
                    pub_date = None
                    if 'date' in selectors:
                        date_elem = element.select_one(selectors['date'])
                        pub_date = date_elem.get_text(strip=True) if date_elem else None
                    
                    if title and link:
                        articles.append({
                            'title': title,
                            'link': link,
                            'published': pub_date or datetime.now().isoformat(),
                            'source': url
                        })
                
                except Exception as e:
                    logger.warning(f"Error parsing article element: {e}")
                    continue
            
            logger.info(f"Scraped {len(articles)} articles from {url}")
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
        
        finally:
            await page.close()
        
        return articles


# Predefined selectors for common medical news sites
SITE_SELECTORS = {
    'healthline': {
        'article': 'article.card',
        'title': 'h2, h3',
        'link': 'a',
        'date': 'time'
    },
    'aaos': {
        'article': '.news-item, article',
        'title': 'h2, h3, .title',
        'link': 'a',
        'date': '.date, time'
    },
    'neurology_today': {
        'article': 'article, .article-item',
        'title': 'h2, h3',
        'link': 'a',
        'date': '.publish-date, time'
    },
    'generic': {
        'article': 'article, .post, .news-item',
        'title': 'h2, h3, .title',
        'link': 'a',
        'date': 'time, .date, .published'
    }
}


async def scrape_url_only_sites(sites: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Scrape all URL-only sites using browser automation
    
    Args:
        sites: List of site dictionaries with 'name' and 'url' keys
        
    Returns:
        Dict mapping site names to lists of articles
    """
    results = {}
    
    async with BrowserScraper() as scraper:
        for site in sites:
            name = site.get('name', '')
            url = site.get('url', '')
            
            if not url:
                continue
            
            # Try to determine the best selector set
            selectors = SITE_SELECTORS.get('generic')
            for key in SITE_SELECTORS:
                if key.lower() in name.lower() or key.lower() in url.lower():
                    selectors = SITE_SELECTORS[key]
                    break
            
            try:
                articles = await scraper.scrape_site(url, selectors)
                results[name] = articles
                logger.info(f"✅ {name}: {len(articles)} articles")
            except Exception as e:
                logger.error(f"❌ {name}: {e}")
                results[name] = []
    
    return results


# Example usage
if __name__ == '__main__':
    async def main():
        # Test with a single site
        async with BrowserScraper() as scraper:
            articles = await scraper.scrape_site(
                'https://www.healthline.com/health-news',
                SITE_SELECTORS['healthline']
            )
            print(f"Found {len(articles)} articles")
            for article in articles[:3]:
                print(f"  - {article['title']}")
    
    asyncio.run(main())
