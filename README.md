# Medical News Feed Scraper

This project aggregates articles from medical news websites you provide and presents them in a simple web UI and JSON API.

## Features

- Automatic RSS/Atom feed discovery from provided website homepages
- Aggregation across multiple sites with deduplication
- FastAPI JSON API: list articles, filter by site and keyword
- Minimal web UI to browse and search
- Simple `sites.yaml` config (you control the sources)
- Fallback homepage scraping when feeds aren’t available (lightweight heuristics)

## Quick Start

### 1) Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure sites

Edit [sites.yaml](sites.yaml) and list your medical news websites (homepages or feed URLs). A sample is included.

### 3) Run the server

```bash
uvicorn main:app --reload
```

Open http://127.0.0.1:8000 in your browser.

## Configuration

The [sites.yaml](sites.yaml) file supports two ways:

- `url`: homepage URL where the scraper will attempt to auto-discover feeds
- `feeds`: explicit feed URLs (RSS/Atom/JSON feeds)

Example:

```yaml
sites:
  - name: WHO News
    url: https://www.who.int/news
  - name: NIH News
    feeds:
      - https://www.nih.gov/news-events/news-releases.xml
  - url: https://www.medscape.com
```

If `name` is omitted, the domain name will be used.

## API Endpoints

- `GET /sites`: List configured sites
- `GET /articles`: Query params: `site`, `q`, `limit` (default 50)

Examples:

```bash
# All articles
curl 'http://127.0.0.1:8000/articles'

# Filter by site name
curl 'http://127.0.0.1:8000/articles?site=NIH%20News'

# Keyword search
curl 'http://127.0.0.1:8000/articles?q=cancer'
```

## Notes

- Respect robots.txt and each site’s terms. This tool prefers official feeds and avoids heavy scraping.
- Network variability: some sites block frequent requests; feeds are refreshed periodically.
- macOS tested; other platforms should work similarly.
- If a site doesn’t expose a feed, the app tries a lightweight homepage scrape to extract headlines. Providing explicit feed URLs in `sites.yaml` yields the most reliable results.
