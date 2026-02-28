#!/usr/bin/env python3
"""
URL validation utilities to prevent SSRF attacks.
Blocks requests to cloud metadata endpoints and internal-only addresses.
"""

import ipaddress
import socket
from urllib.parse import urlparse
from .logger import get_logger

_logger = get_logger("url_validation")

# IP ranges that should never be accessed via test-connection endpoints
BLOCKED_RANGES = [
    ipaddress.ip_network("169.254.0.0/16"),   # Link-local / cloud metadata (AWS, GCP, Azure)
    ipaddress.ip_network("127.0.0.0/8"),       # Loopback
    ipaddress.ip_network("::1/128"),           # IPv6 loopback
    ipaddress.ip_network("fe80::/10"),         # IPv6 link-local
]

# Specific blocked hostnames
BLOCKED_HOSTNAMES = {
    "metadata.google.internal",
    "metadata.google.com",
}


def validate_url(url: str) -> tuple[bool, str]:
    """Validate a URL is safe to make requests to.

    Returns:
        (is_valid, error_message) - is_valid is True if the URL is safe
    """
    if not url:
        return False, "URL is required"

    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL format"

    if parsed.scheme not in ("http", "https"):
        return False, "URL must use http or https"

    hostname = parsed.hostname
    if not hostname:
        return False, "URL must include a hostname"

    # Check blocked hostnames
    if hostname.lower() in BLOCKED_HOSTNAMES:
        _logger.warning(f"Blocked SSRF attempt to metadata hostname: {hostname}")
        return False, "Access to this hostname is not allowed"

    # Resolve hostname and check IP
    try:
        addr_infos = socket.getaddrinfo(hostname, None)
        for family, _, _, _, sockaddr in addr_infos:
            ip = ipaddress.ip_address(sockaddr[0])
            for blocked in BLOCKED_RANGES:
                if ip in blocked:
                    _logger.warning(f"Blocked SSRF attempt: {hostname} resolves to {ip} (in {blocked})")
                    return False, "Access to this address is not allowed"
    except socket.gaierror:
        # DNS resolution failed - let the actual request handle this error
        pass
    except Exception as e:
        _logger.debug(f"URL validation DNS check error for {hostname}: {e}")

    return True, ""
