#!/usr/bin/env python3
"""Audit all data sources and find working RSS feeds."""

import requests
import feedparser
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml
import sys
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import json

# Disable SSL warnings
import urllib3
urllib3.disable_warnings()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

COMMON_FEED_PATHS = [
    "/feed/",
    "/feed",
    "/feeds",
    "/rss",
    "/rss/",
    "/rss.xml",
    "/atom.xml",
    "/index.xml",
    "/feed.xml",
    "/news/rss",
    "/news/feed",
    "/?feed=rss2",
    "/feed/rss2/",
]

def test_feed_url(url: str, timeout: int = 15) -> dict:
    """Test if a URL is a valid RSS/Atom feed."""
    result = {"url": url, "status": "unknown", "articles": 0, "error": None}

    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout, verify=False, allow_redirects=True)
        result["status_code"] = response.status_code

        if response.status_code == 200:
            # Try to parse as feed
            feed = feedparser.parse(response.content)
            if feed.entries:
                result["status"] = "working"
                result["articles"] = len(feed.entries)
                result["feed_title"] = feed.feed.get("title", "Unknown")
            elif feed.bozo and feed.bozo_exception:
                result["status"] = "parse_error"
                result["error"] = str(feed.bozo_exception)[:100]
            else:
                result["status"] = "empty"
        elif response.status_code == 403:
            result["status"] = "blocked"
            result["error"] = "Bot detection / 403 Forbidden"
        elif response.status_code == 404:
            result["status"] = "not_found"
        else:
            result["status"] = f"http_{response.status_code}"
    except requests.exceptions.Timeout:
        result["status"] = "timeout"
    except requests.exceptions.ConnectionError as e:
        result["status"] = "connection_error"
        result["error"] = str(e)[:100]
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)[:100]

    return result

def discover_feeds(url: str) -> list:
    """Try to discover RSS/Atom feeds from a URL."""
    feeds = []

    try:
        response = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        if response.status_code != 200:
            return feeds

        soup = BeautifulSoup(response.text, "html.parser")

        # Look for link tags
        for link in soup.find_all("link", rel=lambda x: x and "alternate" in x):
            href = link.get("href")
            link_type = link.get("type", "")
            if href and ("rss" in link_type or "atom" in link_type or "xml" in link_type):
                full_url = urljoin(url, href)
                if full_url not in feeds:
                    feeds.append(full_url)

        # Look for common feed paths
        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        for path in COMMON_FEED_PATHS:
            feed_url = base_url + path
            if feed_url not in feeds:
                feeds.append(feed_url)

    except Exception as e:
        pass

    return feeds

def audit_site(site: dict) -> dict:
    """Audit a single site and return results."""
    name = site.get("name", "Unknown")
    url = site.get("url", "")
    configured_feeds = site.get("feeds", [])

    result = {
        "name": name,
        "url": url,
        "configured_feeds": configured_feeds,
        "working_feeds": [],
        "failed_feeds": [],
        "discovered_feeds": [],
        "status": "unknown"
    }

    print(f"\n{'='*60}")
    print(f"Auditing: {name}")
    print(f"URL: {url}")
    sys.stdout.flush()

    # Test configured feeds
    for feed_url in configured_feeds:
        test = test_feed_url(feed_url)
        if test["status"] == "working":
            result["working_feeds"].append({
                "url": feed_url,
                "articles": test["articles"],
                "title": test.get("feed_title", "")
            })
            print(f"  ✓ WORKING: {feed_url} ({test['articles']} articles)")
        else:
            result["failed_feeds"].append({
                "url": feed_url,
                "status": test["status"],
                "error": test.get("error", "")
            })
            print(f"  ✗ FAILED: {feed_url} - {test['status']}")

    # If no working feeds, try to discover
    if not result["working_feeds"] and url:
        print(f"  Discovering feeds from {url}...")
        discovered = discover_feeds(url)

        for feed_url in discovered[:10]:  # Limit discovery attempts
            if feed_url in configured_feeds:
                continue
            test = test_feed_url(feed_url)
            if test["status"] == "working":
                result["discovered_feeds"].append({
                    "url": feed_url,
                    "articles": test["articles"],
                    "title": test.get("feed_title", "")
                })
                print(f"  ✓ DISCOVERED: {feed_url} ({test['articles']} articles)")

    # Determine overall status
    if result["working_feeds"]:
        result["status"] = "working"
        total = sum(f["articles"] for f in result["working_feeds"])
        print(f"  STATUS: WORKING ({len(result['working_feeds'])} feeds, {total} articles)")
    elif result["discovered_feeds"]:
        result["status"] = "needs_update"
        print(f"  STATUS: NEEDS UPDATE (discovered {len(result['discovered_feeds'])} new feeds)")
    else:
        result["status"] = "broken"
        print(f"  STATUS: BROKEN (no working feeds found)")

    sys.stdout.flush()
    return result

def main():
    # Load sites
    with open("sites.yaml", "r") as f:
        config = yaml.safe_load(f)

    sites = config.get("sites", [])
    print(f"Auditing {len(sites)} sites...")

    results = {
        "total": len(sites),
        "working": 0,
        "needs_update": 0,
        "broken": 0,
        "sites": []
    }

    for site in sites:
        result = audit_site(site)
        results["sites"].append(result)

        if result["status"] == "working":
            results["working"] += 1
        elif result["status"] == "needs_update":
            results["needs_update"] += 1
        else:
            results["broken"] += 1

    # Summary
    print("\n" + "="*60)
    print("AUDIT SUMMARY")
    print("="*60)
    print(f"Total sites: {results['total']}")
    print(f"Working: {results['working']}")
    print(f"Needs update: {results['needs_update']}")
    print(f"Broken: {results['broken']}")

    # List broken sites
    print("\n--- BROKEN SITES ---")
    for site in results["sites"]:
        if site["status"] == "broken":
            print(f"  - {site['name']}")

    # List sites needing updates
    print("\n--- SITES NEEDING UPDATES ---")
    for site in results["sites"]:
        if site["status"] == "needs_update":
            print(f"  - {site['name']}")
            for feed in site["discovered_feeds"]:
                print(f"    NEW: {feed['url']} ({feed['articles']} articles)")

    # Save results
    with open("/Users/mustafaahmed/Desktop/source_audit_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nFull results saved to: /Users/mustafaahmed/Desktop/source_audit_results.json")

if __name__ == "__main__":
    main()
