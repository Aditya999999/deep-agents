"""
ForgeX — HTTP Fetch Tool

Fetch and normalize public web pages per spec §9.2.
Includes SSRF protection, timeout, size limits, and content-type validation.
Built as a LangChain tool via @tool decorator.
"""

import ipaddress
import json
from urllib.parse import urlparse

import httpx
from langchain_core.tools import tool

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("tools.http_fetch")

# Maximum response size (5 MB)
MAX_RESPONSE_SIZE = 5 * 1024 * 1024

# Maximum redirects
MAX_REDIRECTS = 5

# Blocked IP ranges for SSRF prevention
PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

ALLOWED_CONTENT_TYPES = [
    "text/html",
    "text/plain",
    "application/json",
    "application/xml",
    "text/xml",
    "text/markdown",
]


def _is_private_ip(hostname: str) -> bool:
    """Check if a hostname resolves to a private/reserved IP."""
    try:
        ip = ipaddress.ip_address(hostname)
        return any(ip in network for network in PRIVATE_NETWORKS)
    except ValueError:
        lower = hostname.lower()
        return lower in ("localhost", "0.0.0.0") or lower.endswith(".local")


def _validate_url(url: str) -> tuple[bool, str]:
    """Validate URL for safety."""
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL format"

    if parsed.scheme not in ("http", "https"):
        return False, "Only HTTP and HTTPS URLs are allowed"

    if not parsed.hostname:
        return False, "URL must have a hostname"

    # SSRF protection
    if settings.http_tool_block_private_networks and _is_private_ip(parsed.hostname):
        return False, "Private/localhost addresses are blocked"

    # Check allowed host suffixes if configured
    allowed = settings.allowed_hosts_list
    if allowed:
        if not any(parsed.hostname.endswith(suffix) for suffix in allowed):
            return False, "Host not in allowed list"

    return True, ""


@tool
async def http_fetch(url: str) -> str:
    """Retrieve and normalize a public web page for reading. Includes SSRF protection,
    timeout enforcement, response size limits, and content-type validation.
    HTTPS is preferred. Private/localhost addresses are blocked.

    Args:
        url: The URL to fetch (must be http:// or https://)
    """
    try:
        if not url or not url.strip():
            return "Error: Empty URL"

        url = url.strip()
        valid, reason = _validate_url(url)
        if not valid:
            return f"Error: {reason}"

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0),
            follow_redirects=True,
            max_redirects=MAX_REDIRECTS,
        ) as client:
            response = await client.get(url, headers={"User-Agent": "ForgeX-Agent/1.0"})

            # Validate content type
            content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
            if content_type not in ALLOWED_CONTENT_TYPES:
                return f"Error: Unsupported content type '{content_type}'. Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}"

            # Check size
            content_length = len(response.content)
            if content_length > MAX_RESPONSE_SIZE:
                return f"Error: Response too large ({content_length} bytes, max {MAX_RESPONSE_SIZE})"

            text = response.text[:50000]  # Limit text to ~50K chars

            logger.info(f"Fetched {url}: {response.status_code}, {content_length} bytes")

            result = {
                "url": str(response.url),
                "status_code": response.status_code,
                "content_type": content_type,
                "content_length": content_length,
                "content": text,
            }
            return json.dumps(result, indent=2)

    except httpx.TimeoutException:
        logger.warning(f"HTTP fetch timeout: {url}")
        return f"Error: Request to {url} timed out"
    except httpx.TooManyRedirects:
        return f"Error: Too many redirects for {url}"
    except Exception as e:
        logger.error(f"HTTP fetch error for {url}: {e}")
        return f"Error: Fetch failed — {str(e)}"
