import asyncio
import aiohttp
import feedparser
import yaml
from urllib.parse import urlparse
import time

async def test_feed(session, feed_url, timeout=10):
    """Test if a feed URL is accessible and returns articles"""
    try:
        async with session.get(feed_url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
            if response.status == 200:
                content = await response.text()
                feed = feedparser.parse(content)
                return {
                    'status': 'working',
                    'articles': len(feed.entries),
                    'status_code': 200
                }
            else:
                return {
                    'status': 'error',
                    'articles': 0,
                    'status_code': response.status
                }
    except asyncio.TimeoutError:
        return {'status': 'timeout', 'articles': 0, 'status_code': 0}
    except Exception as e:
        return {'status': 'error', 'articles': 0, 'status_code': 0, 'error': str(e)[:50]}

async def test_site(site, session):
    """Test a single site configuration"""
    name = site.get('name', 'Unknown')
    feeds = site.get('feeds', [])
    url = site.get('url', '')
    
    results = {
        'name': name,
        'url': url,
        'feeds_count': len(feeds),
        'feed_results': []
    }
    
    if feeds:
        for feed_url in feeds:
            result = await test_feed(session, feed_url)
            results['feed_results'].append({
                'feed_url': feed_url,
                **result
            })
    
    return results

async def main():
    with open('sites.yaml', 'r') as f:
        data = yaml.safe_load(f)
    
    sites = data.get('sites', [])
    
    # Test only first 20 sites for speed
    test_sites = sites[:20]
    
    print(f"Testing {len(test_sites)} sites (sample)...\n")
    
    async with aiohttp.ClientSession() as session:
        tasks = [test_site(site, session) for site in test_sites]
        results = await asyncio.gather(*tasks)
    
    working = 0
    total_articles = 0
    
    for result in results:
        status_icon = "✅" if any(f['status'] == 'working' for f in result['feed_results']) else "❌"
        articles = sum(f['articles'] for f in result['feed_results'])
        
        if articles > 0:
            working += 1
            total_articles += articles
        
        print(f"{status_icon} {result['name']}")
        if result['feeds_count'] > 0:
            for feed in result['feed_results']:
                print(f"   - {feed['status']}: {feed['articles']} articles (HTTP {feed['status_code']})")
        else:
            print(f"   - No RSS feeds configured (URL only)")
    
    print(f"\n{'='*60}")
    print(f"Summary: {working}/{len(test_sites)} sites working")
    print(f"Total articles found: {total_articles}")

if __name__ == '__main__':
    asyncio.run(main())
