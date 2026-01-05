"""Test security module."""

import pytest
import sys
sys.path.insert(0, '/home/ubuntu/news_feed_review')

from security import validate_url, sanitize_for_xml


class TestURLValidation:
    """Test SSRF protection."""
    
    def test_valid_https_url(self):
        """Test that valid HTTPS URLs are accepted."""
        assert validate_url("https://www.example.com") == True
        assert validate_url("https://www.google.com") == True
        assert validate_url("https://api.github.com/repos") == True
    
    def test_valid_http_url(self):
        """Test that valid HTTP URLs are accepted."""
        assert validate_url("http://www.example.com") == True
    
    def test_localhost_blocked(self):
        """Test that localhost is blocked."""
        assert validate_url("http://localhost:8000") == False
        assert validate_url("http://localhost") == False
        assert validate_url("http://127.0.0.1") == False
    
    def test_private_ip_blocked(self):
        """Test that private IPs are blocked."""
        assert validate_url("http://192.168.1.1") == False
        assert validate_url("http://10.0.0.1") == False
        assert validate_url("http://172.16.0.1") == False
    
    def test_invalid_scheme_blocked(self):
        """Test that non-HTTP schemes are blocked."""
        assert validate_url("ftp://example.com") == False
        assert validate_url("file:///etc/passwd") == False


class TestXMLSanitization:
    """Test XML sanitization."""
    
    def test_script_tag_escaped(self):
        """Test that script tags are escaped."""
        result = sanitize_for_xml('<script>alert("xss")</script>')
        assert "&lt;script&gt;" in result
    
    def test_ampersand_escaped(self):
        """Test that ampersands are escaped."""
        result = sanitize_for_xml("A & B")
        assert "A &amp; B" == result
    
    def test_empty_string(self):
        """Test that empty strings are handled."""
        assert sanitize_for_xml("") == ""
