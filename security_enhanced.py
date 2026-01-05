"""Enhanced security utilities for URL validation and sanitization."""

import ipaddress
import logging
import hashlib
import hmac
from urllib.parse import urlparse
from typing import Optional

logger = logging.getLogger(__name__)


def validate_url(url: str) -> bool:
    """
    Validate URL to prevent SSRF attacks.

    Blocks:
    - Non-HTTP(S) schemes
    - Private IP addresses
    - Localhost addresses
    - Internal network ranges
    
    Args:
        url: URL to validate
    
    Returns:
        True if URL is safe, False otherwise
    """
    if not isinstance(url, str):
        logger.warning(f"Invalid URL type: {type(url)}")
        return False
    
    try:
        parsed = urlparse(url)

        # Only allow http/https schemes
        if parsed.scheme not in ('http', 'https'):
            logger.warning(f"Blocked URL with invalid scheme: {url}")
            return False

        # Extract hostname/IP
        hostname = parsed.netloc.split(':')[0] if ':' in parsed.netloc else parsed.netloc

        # Block localhost variations
        if hostname.lower() in ('localhost', '127.0.0.1', '0.0.0.0', '[::1]', '::1'):
            logger.warning(f"Blocked localhost URL: {url}")
            return False

        # Check if it's an IP address
        try:
            ip = ipaddress.ip_address(hostname)
            # Block private and loopback IPs
            if ip.is_private or ip.is_loopback or ip.is_reserved:
                logger.warning(f"Blocked private/reserved IP: {url}")
                return False
        except ValueError:
            # Not an IP address - it's a domain name, which is fine
            pass

        return True
    except Exception as e:
        logger.error(f"URL validation error for {url}: {e}")
        return False


def sanitize_for_xml(text: Optional[str]) -> str:
    """
    Sanitize text for safe XML parsing.
    
    Args:
        text: Text to sanitize
    
    Returns:
        Sanitized text safe for XML
    """
    if not text:
        return ""
    
    if not isinstance(text, str):
        text = str(text)
    
    # Remove potentially dangerous XML entities
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&apos;'))


def sanitize_html(html: Optional[str]) -> str:
    """
    Sanitize HTML to prevent XSS attacks.
    
    Args:
        html: HTML to sanitize
    
    Returns:
        Sanitized HTML
    """
    if not html:
        return ""
    
    # Remove script tags and event handlers
    import re
    
    # Remove script tags
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove event handlers
    html = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', html, flags=re.IGNORECASE)
    html = re.sub(r'\s*on\w+\s*=\s*[^\s>]*', '', html, flags=re.IGNORECASE)
    
    # Remove iframe tags
    html = re.sub(r'<iframe[^>]*>.*?</iframe>', '', html, flags=re.DOTALL | re.IGNORECASE)
    
    return html


def generate_request_signature(data: str, secret: str) -> str:
    """
    Generate HMAC signature for request validation.
    
    Args:
        data: Data to sign
        secret: Secret key
    
    Returns:
        HMAC signature
    """
    return hmac.new(
        secret.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()


def verify_request_signature(data: str, signature: str, secret: str) -> bool:
    """
    Verify HMAC signature for request validation.
    
    Args:
        data: Original data
        signature: Signature to verify
        secret: Secret key
    
    Returns:
        True if signature is valid, False otherwise
    """
    expected_signature = generate_request_signature(data, secret)
    return hmac.compare_digest(signature, expected_signature)


def rate_limit_key(identifier: str, window: int = 60) -> str:
    """
    Generate a rate limiting key based on identifier and time window.
    
    Args:
        identifier: User/IP identifier
        window: Time window in seconds
    
    Returns:
        Rate limit key
    """
    import time
    current_window = int(time.time() / window)
    return f"{identifier}:{current_window}"
