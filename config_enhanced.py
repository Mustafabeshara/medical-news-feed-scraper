"""Enhanced configuration management with validation."""

from dataclasses import dataclass, field
from typing import Tuple
import os
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScraperConfig:
    """Configuration for news scraper with validation."""
    
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
    concurrent_requests: int = 10
    requests_per_batch: int = 5
    batch_delay_seconds: float = 0.5
    
    # API settings
    api_rate_limit: str = "30/minute"
    refresh_interval_sec: int = 900  # 15 minutes
    
    # Security
    allowed_schemes: Tuple[str, ...] = field(default_factory=lambda: ("http", "https"))
    blocked_hosts: Tuple[str, ...] = field(
        default_factory=lambda: (
            "localhost", "127.0.0.1", "0.0.0.0",
            "169.254.0.0/16", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"
        )
    )
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Environment-based overrides
    def __post_init__(self):
        """Load configuration from environment variables."""
        self.timeout_seconds = int(os.getenv("TIMEOUT_SECONDS", self.timeout_seconds))
        self.max_retries = int(os.getenv("MAX_RETRIES", self.max_retries))
        self.concurrent_requests = int(os.getenv("CONCURRENT_REQUESTS", self.concurrent_requests))
        self.refresh_interval_sec = int(os.getenv("REFRESH_INTERVAL_SEC", self.refresh_interval_sec))
        self.log_level = os.getenv("LOG_LEVEL", self.log_level)
        
        # Validate values
        if self.timeout_seconds < 1 or self.timeout_seconds > 300:
            raise ValueError("timeout_seconds must be between 1 and 300")
        if self.max_retries < 0 or self.max_retries > 10:
            raise ValueError("max_retries must be between 0 and 10")
        if self.concurrent_requests < 1 or self.concurrent_requests > 100:
            raise ValueError("concurrent_requests must be between 1 and 100")
        if self.refresh_interval_sec < 60 or self.refresh_interval_sec > 86400:
            raise ValueError("refresh_interval_sec must be between 60 and 86400")
        
        logger.info(f"Configuration loaded: timeout={self.timeout_seconds}s, "
                   f"retries={self.max_retries}, concurrent={self.concurrent_requests}")


# Create global CONFIG instance
CONFIG = ScraperConfig()
