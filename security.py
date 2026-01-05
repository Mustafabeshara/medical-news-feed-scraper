"""Security utilities for URL validation and sanitization."""
import ipaddress
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def validate_url(url: str) -> bool:
    """
    Validate URL to prevent SSRF attacks.

    Blocks:
    - Non-HTTP(S) schemes
    - Private IP addresses
    - Localhost addresses
    - Internal network ranges
    """
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


def sanitize_for_xml(text: str) -> str:
    """Sanitize text for safe XML parsing."""
    if not text:
        return ""
    # Remove potentially dangerous XML entities
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')
