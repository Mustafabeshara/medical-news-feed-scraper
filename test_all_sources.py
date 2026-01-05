import asyncio
import aiohttp
import feedparser
import yaml
from urllib.parse import urlparse
import json

async def test_feed(session, feed_url, timeout=15):
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
        return {'status': 'error', 'articles': 0, 'status_code': 0, 'error': str(e)[:100]}

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
    
    print(f"Testing ALL {len(sites)} sites...\n")
    print("This may take a few minutes...\n")
    
    async with aiohttp.ClientSession() as session:
        # Process in batches to avoid overwhelming the system
        batch_size = 10
        all_results = []
        
        for i in range(0, len(sites), batch_size):
            batch = sites[i:i+batch_size]
            print(f"Testing batch {i//batch_size + 1}/{(len(sites)-1)//batch_size + 1}...")
            tasks = [test_site(site, session) for site in batch]
            results = await asyncio.gather(*tasks)
            all_results.extend(results)
            await asyncio.sleep(1)  # Brief pause between batches
    
    # Analyze results
    working = []
    errors = []
    no_feeds = []
    total_articles = 0
    
    print("\n" + "="*80)
    print("DETAILED RESULTS")
    print("="*80 + "\n")
    
    for result in all_results:
        has_working_feed = any(f['status'] == 'working' and f['articles'] > 0 for f in result['feed_results'])
        articles = sum(f['articles'] for f in result['feed_results'])
        
        if result['feeds_count'] == 0:
            status_icon = "⚠️"
            no_feeds.append(result)
        elif has_working_feed:
            status_icon = "✅"
            working.append(result)
            total_articles += articles
        else:
            status_icon = "❌"
            errors.append(result)
        
        print(f"{status_icon} {result['name']}")
        if result['feeds_count'] > 0:
            for feed in result['feed_results']:
                status_detail = f"{feed['status']}: {feed['articles']} articles (HTTP {feed['status_code']})"
                if 'error' in feed:
                    status_detail += f" - {feed['error'][:50]}"
                print(f"   └─ {status_detail}")
        else:
            print(f"   └─ No RSS feeds configured (URL only)")
        print()
    
    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total Sites: {len(all_results)}")
    print(f"✅ Working: {len(working)} ({len(working)/len(all_results)*100:.1f}%)")
    print(f"❌ Errors: {len(errors)} ({len(errors)/len(all_results)*100:.1f}%)")
    print(f"⚠️  No Feeds: {len(no_feeds)} ({len(no_feeds)/len(all_results)*100:.1f}%)")
    print(f"📰 Total Articles: {total_articles:,}")
    print()
    
    # Save detailed results to JSON
    with open('test_results.json', 'w') as f:
        json.dump({
            'total': len(all_results),
            'working': len(working),
            'errors': len(errors),
            'no_feeds': len(no_feeds),
            'total_articles': total_articles,
            'working_sites': [{'name': s['name'], 'articles': sum(f['articles'] for f in s['feed_results'])} for s in working],
            'error_sites': [{'name': s['name'], 'feeds': s['feed_results']} for s in errors],
            'no_feed_sites': [{'name': s['name'], 'url': s['url']} for s in no_feeds]
        }, f, indent=2)
    
    print("✅ Detailed results saved to test_results.json")

if __name__ == '__main__':
    asyncio.run(main())
