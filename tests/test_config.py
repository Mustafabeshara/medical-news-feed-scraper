"""Test configuration module."""

import pytest
import sys
sys.path.insert(0, '/home/ubuntu/news_feed_review')

from config import CONFIG


class TestConfiguration:
    """Test configuration settings."""
    
    def test_config_exists(self):
        """Test that CONFIG object exists."""
        assert CONFIG is not None
    
    def test_timeout_seconds(self):
        """Test timeout configuration."""
        assert CONFIG.timeout_seconds > 0
        assert CONFIG.timeout_seconds <= 300
    
    def test_max_retries(self):
        """Test retry configuration."""
        assert CONFIG.max_retries >= 0
        assert CONFIG.max_retries <= 10
    
    def test_concurrent_requests(self):
        """Test concurrent request configuration."""
        assert CONFIG.concurrent_requests > 0
        assert CONFIG.concurrent_requests <= 100
    
    def test_refresh_interval(self):
        """Test refresh interval configuration."""
        assert CONFIG.refresh_interval_sec > 0
        assert CONFIG.refresh_interval_sec <= 86400  # 1 day max
    
    def test_allowed_schemes(self):
        """Test allowed schemes configuration."""
        assert "http" in CONFIG.allowed_schemes
        assert "https" in CONFIG.allowed_schemes
    
    def test_blocked_hosts(self):
        """Test blocked hosts configuration."""
        assert "localhost" in CONFIG.blocked_hosts
        assert "127.0.0.1" in CONFIG.blocked_hosts
