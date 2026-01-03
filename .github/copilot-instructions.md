# Copilot Instructions for Medical News Feed Scraper

These instructions help AI coding agents quickly contribute to this FastAPI-based news aggregator. Focus on project-specific patterns, data flow, and workflows reflected in the current codebase.

## Architecture Overview

- **FastAPI app**: See [main.py](main.py). Provides `GET /health`, `GET /sites`, `GET /articles`, `GET /export/word`, `GET /export/pdf`, and serves [static/index.html](static/index.html) at `/`.
- **Aggregator layer**: See [aggregator.py](aggregator.py).
  - Feed discovery (`discover_feeds`), feed parsing (`parse_feed`), homepage scraping (`scrape_homepage_articles`).
  - Concurrency: `fetch_all_sites()` uses `asyncio.Semaphore` sized by [config.py](config.py) `CONFIG.concurrent_requests`.
  - Security: All outbound requests go through `_safe_get()` which calls [security.py](security.py) `validate_url()` for SSRF protection.
  - Entity enrichment: `enrich_article()` in [entity_extractor.py](entity_extractor.py) adds `companies` and `products` to each article.
- **Config**: Centralized settings via `CONFIG` in [config.py](config.py). Avoid magic numbers; read values from the dataclass.
- **Data flow**:
  - On startup, `load_config()` reads [sites.yaml](sites.yaml); `refresher_task()` periodically calls `fetch_all_sites()`.
  - Results are stored in in-memory caches in [main.py](main.py): `_cache_articles_by_site` and `_cache_last_refresh`.
  - API flattens + filters via `filter_articles()` in [aggregator.py](aggregator.py).

## Article Schema (dictionary keys)

- `title`, `link`, `summary`, `published`, `image`, `source`, `feed`, `site`, `companies`, `products`.
- Filtering combines `title + summary + source` substring match; see `filter_articles()` in [aggregator.py](aggregator.py).

## Developer Workflows

- **Install**:
  - Create venv and install: see [README.md](README.md) and [start_demo.sh](start_demo.sh).
  - Dependencies listed in [requirements.txt](requirements.txt).
- **Run**:
  - Dev server: `uvicorn main:app --reload` (from repo root).
  - One-click demo: `./start_demo.sh` (creates venv if missing, installs deps, starts server).
- **Status/Health**:
  - Quick check: `./CHECK_STATUS.sh` to see `/health` metrics and whether port 8000 is up.
- **Testing feeds/sites**:
  - Diagnostic runner: [test_sites.py](test_sites.py).
    - Examples:
      - `python test_sites.py --quick`
      - `python test_sites.py --site "WHO News"`
      - `python test_sites.py --browser` (uses Playwright when available)

## Configuration Patterns

- Sources in [sites.yaml](sites.yaml):
  - `url`: homepage for feed auto-discovery; `feeds`: explicit RSS/Atom/JSON feed URLs.
  - `name` optional; falls back to domain.
- Override config path via env var `SITES_CONFIG` (read in [main.py](main.py)).
- Adjust concurrency, timeouts, retry rules in [config.py](config.py) via `ScraperConfig`.

## Security & Safety

- Always route outbound HTTP through `_safe_get()` in [aggregator.py](aggregator.py) to enforce `validate_url()` and common retry/backoff.
- XML/HTML parsing should use current safe patterns:
  - `feedparser` + `BeautifulSoup` are used; summaries are sanitized before display and export.
- Respect robots/terms; prefer official feeds; homepage scraping is a lightweight fallback.

## Browser Automation (optional)

- Some domains need headless browser rendering or block scrapers.
- Playwright usage guarded by `PLAYWRIGHT_AVAILABLE` and `_needs_browser()`; see `browser_fetch_feed()` / `browser_scrape_homepage()` in [aggregator.py](aggregator.py).
- Keep browser automation contained to these helpers; avoid spreading Playwright usage elsewhere.

## Web UI

- Minimal UI in [static/index.html](static/index.html) uses `/sites` and `/articles` to populate filters and grid.
- Exports via `/export/word` and `/export/pdf` route handlers in [main.py](main.py) using `python-docx` and `reportlab`.

## Contributing Patterns

- Add new sources by editing [sites.yaml](sites.yaml). Prefer explicit `feeds` if auto-discovery fails.
- When adding scraping heuristics, keep selection precise and avoid navigation/noise links (follow patterns in `scrape_homepage_articles`).
- When changing performance behavior, adjust `CONFIG.concurrent_requests` and related delay knobs; keep `fetch_all_sites()` semaphore logic.
- Logging follows `logger` in [aggregator.py](aggregator.py). Use structured messages and avoid `print` except for startup/demo.

## Non-Obvious Tips

- Initial refresh is async and periodic; UI may show "Last refresh: Not yet" just after startup.
- Many publisher RSS endpoints shift or deprecate; use [test_sites.py](test_sites.py) to discover working feeds and update [sites.yaml](sites.yaml).
- `slowapi` is present for future API rate limiting but not currently wired into [main.py](main.py).

---

If any section is unclear or you need deeper examples (e.g., extending entity extraction or adding a specialty site), tell me which part to refine and I'll iterate.
