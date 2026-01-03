"""Configuration management for Medical News Feed Scraper."""
from dataclasses import dataclass
import os


@dataclass
class ScraperConfig:
    """Configuration for news scraper."""
    # HTTP settings
    timeout_seconds: int = 20
    max_retries: int = 2
    retry_delay_seconds: int = 1

    # Feed discovery
    max_common_paths_to_check: int = 8
    max_feeds_per_site: int = 3

    # Scraping limits
    max_articles_per_site: int = 50
    browser_render_delay_seconds: float = 1.0

    # Rate limiting
    concurrent_requests: int = 10  # Concurrent site fetches
    requests_per_batch: int = 5
    batch_delay_seconds: float = 0.5

    # API settings
    api_rate_limit: str = "30/minute"  # Requests per minute per IP
    refresh_interval_sec: int = 900  # 15 minutes

    # Security
    allowed_schemes: tuple = ("http", "https")
    blocked_hosts: tuple = ("localhost", "127.0.0.1", "0.0.0.0", "169.254.0.0/16", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")


CONFIG = ScraperConfig()
