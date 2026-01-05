#!/usr/bin/env python3
"""
Diagnostic script to test medical news feed sources.
Run this to identify which sites are working and which need attention.

Usage:
    python test_sites.py                    # Test all sites
    python test_sites.py --site "WHO News" # Test specific site
    python test_sites.py --quick            # Quick test (first 10 sites)
    python test_sites.py --browser          # Test with browser automation
"""

import argparse
import asyncio
import logging
import sys
import yaml

# Reduce noise from warnings
logging.basicConfig(level=logging.ERROR, format='%(message)s')

from aggregator import (
    discover_feeds, scrape_homepage_articles, _safe_get, parse_feed,
    _needs_browser, browser_fetch_feed, browser_scrape_homepage,
    PLAYWRIGHT_AVAILABLE
)


async def test_single_site(site: dict, verbose: bool = False, use_browser: bool = False) -> dict:
    """Test a single site and return results."""
    name = site.get('name', 'Unknown')
    url = site.get('url')
    feeds = site.get('feeds', [])

    result = {
        'name': name,
        'url': url,
        'feeds': feeds,
        'status': 'unknown',
        'articles': 0,
        'issues': [],
        'working_feeds': [],
        'discovered_feeds': [],
        'browser_used': False,
    }

    # Test explicit feeds first
    for feed_url in feeds:
        articles, _ = parse_feed(feed_url)

        # Try browser if no articles and browser mode enabled
        if not articles and use_browser and _needs_browser(feed_url) and PLAYWRIGHT_AVAILABLE:
            if verbose:
                print(f"    🌐 Trying browser for feed: {feed_url}")
            articles, _ = await browser_fetch_feed(feed_url)
            if articles:
                result['browser_used'] = True

        if articles:
            result['articles'] += len(articles)
            result['working_feeds'].append(feed_url)
            if verbose:
                print(f"    ✓ Feed OK ({len(articles)} articles): {feed_url}")
        else:
            result['issues'].append(f"Feed empty or inaccessible: {feed_url}")

    # Test URL and discover feeds
    if url:
        resp = _safe_get(url)
        if resp is None:
            result['issues'].append(f"URL inaccessible: {url}")

            # Try browser if URL inaccessible and browser mode enabled
            if use_browser and _needs_browser(url) and PLAYWRIGHT_AVAILABLE:
                if verbose:
                    print(f"    🌐 Trying browser scrape for: {url}")
                scraped = await browser_scrape_homepage(url, limit=10)
                if scraped:
                    result['articles'] += len(scraped)
                    result['browser_used'] = True
                    result['issues'] = [i for i in result['issues'] if 'URL inaccessible' not in i]
                    if verbose:
                        print(f"    ✓ Browser scrape: {len(scraped)} articles")
        else:
            discovered = discover_feeds(url)
            result['discovered_feeds'] = discovered

            if verbose and discovered:
                print(f"    Discovered {len(discovered)} feeds")

            # Parse discovered feeds (skip if already have articles)
            if result['articles'] == 0:
                for feed_url in discovered[:3]:  # Limit to first 3
                    if feed_url not in feeds:  # Don't retest explicit feeds
                        articles, _ = parse_feed(feed_url)
                        if articles:
                            result['articles'] += len(articles)
                            result['working_feeds'].append(feed_url)

                # Try homepage scraping if still no articles
                if result['articles'] == 0:
                    scraped = scrape_homepage_articles(url, limit=10)

                    # Try browser scraping if regular scraping failed
                    if not scraped and use_browser and _needs_browser(url) and PLAYWRIGHT_AVAILABLE:
                        if verbose:
                            print(f"    🌐 Trying browser scrape for: {url}")
                        scraped = await browser_scrape_homepage(url, limit=10)
                        if scraped:
                            result['browser_used'] = True

                    if scraped:
                        result['articles'] += len(scraped)
                        if verbose:
                            print(f"    Homepage scraping: {len(scraped)} articles")
                    else:
                        result['issues'].append("Homepage scraping failed")

    # Determine status
    if result['articles'] > 0:
        result['status'] = 'working'
    elif result['issues']:
        result['status'] = 'failed'
    else:
        result['status'] = 'no_articles'

    return result


async def main_async(args, sites):
    """Async main function."""
    working = []
    failed = []
    no_articles = []
    browser_helped = []

    for i, site in enumerate(sites):
        name = site.get('name', 'Unknown')
        print(f"[{i+1:02d}/{len(sites)}] Testing: {name}")

        result = await test_single_site(site, verbose=args.verbose, use_browser=args.browser)

        if result['status'] == 'working':
            browser_note = " (🌐 browser)" if result['browser_used'] else ""
            print(f"    ✓ {result['articles']} articles{browser_note}")
            working.append(result)
            if result['browser_used']:
                browser_helped.append(result)
        elif result['status'] == 'failed':
            print(f"    ✗ Failed: {result['issues'][0] if result['issues'] else 'Unknown'}")
            failed.append(result)
        else:
            print(f"    ⚠ No articles found")
            no_articles.append(result)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✓ Working: {len(working)} sites")
    if browser_helped:
        print(f"  🌐 Browser automation helped: {len(browser_helped)} sites")
    print(f"⚠ No articles: {len(no_articles)} sites")
    print(f"✗ Failed: {len(failed)} sites")

    if failed:
        print("\n--- FAILED SITES ---")
        for r in failed:
            print(f"\n{r['name']}")
            print(f"  URL: {r['url']}")
            if r['feeds']:
                print(f"  Feeds: {r['feeds']}")
            for issue in r['issues'][:3]:
                print(f"  Issue: {issue}")

    if no_articles:
        print("\n--- SITES WITH NO ARTICLES ---")
        for r in no_articles:
            print(f"\n{r['name']}")
            print(f"  URL: {r['url']}")
            if r['discovered_feeds']:
                print(f"  Discovered feeds: {r['discovered_feeds'][:2]}")
            print(f"  Try: Search for '{r['name']} RSS feed' to find correct URL")

    print("\n--- RECOMMENDATIONS ---")
    if not args.browser:
        print("1. Run with --browser flag to enable browser automation for bot-protected sites")
    print("2. For empty feeds: Feed URL may have changed, search for new RSS URL")
    print("3. For no articles: Try adding explicit feed URLs to sites.yaml")

    return 0 if not failed else 1


def main():
    parser = argparse.ArgumentParser(description='Test medical news feed sources')
    parser.add_argument('--site', type=str, help='Test specific site by name')
    parser.add_argument('--quick', action='store_true', help='Quick test (first 10 sites)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--browser', '-b', action='store_true', help='Enable browser automation for bot-protected sites')
    parser.add_argument('--config', type=str, default='sites.yaml', help='Config file path')
    args = parser.parse_args()

    # Load config
    with open(args.config, 'r') as f:
        data = yaml.safe_load(f)
        sites = data.get('sites', [])

    print(f"Loaded {len(sites)} sites from {args.config}")
    if args.browser:
        if PLAYWRIGHT_AVAILABLE:
            print("🌐 Browser automation ENABLED")
        else:
            print("⚠ Playwright not installed - browser automation disabled")
    print()

    # Filter sites if needed
    if args.site:
        sites = [s for s in sites if s.get('name', '').lower() == args.site.lower()]
        if not sites:
            print(f"Site '{args.site}' not found")
            return 1
    elif args.quick:
        sites = sites[:10]

    return asyncio.run(main_async(args, sites))


if __name__ == '__main__':
    sys.exit(main())
