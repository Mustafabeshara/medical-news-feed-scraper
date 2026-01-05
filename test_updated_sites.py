import asyncio
import aiohttp
import feedparser
import yaml

async def test_feed(session, feed_url):
    try:
        async with session.get(feed_url, timeout=aiohttp.ClientTimeout(total=15)) as response:
            if response.status == 200:
                content = await response.text()
                feed = feedparser.parse(content)
                return len(feed.entries)
            return 0
    except:
        return 0

async def main():
    with open('sites_updated.yaml', 'r') as f:
        data = yaml.safe_load(f)
    
    sites = data.get('sites', [])
    
    print(f"Testing {len(sites)} updated sites...\n")
    
    async with aiohttp.ClientSession() as session:
        total_articles = 0
        working_count = 0
        
        for site in sites:
            name = site.get('name', 'Unknown')
            feeds = site.get('feeds', [])
            
            if feeds:
                articles = 0
                for feed_url in feeds:
                    count = await test_feed(session, feed_url)
                    articles += count
                
                if articles > 0:
                    print(f"✅ {name}: {articles} articles")
                    working_count += 1
                    total_articles += articles
                else:
                    print(f"⚠️  {name}: 0 articles")
            else:
                print(f"🌐 {name}: URL only (browser scraping)")
        
        print(f"\n{'='*60}")
        print(f"Working RSS feeds: {working_count}/{len([s for s in sites if s.get('feeds')])}")
        print(f"Total articles: {total_articles:,}")
        print(f"URL-only sites: {len([s for s in sites if not s.get('feeds')])}")

if __name__ == '__main__':
    asyncio.run(main())
