#!/usr/bin/env python3
"""
URL validation utilities to prevent SSRF attacks.
Blocks requests to cloud metadata endpoints and internal-only addresses.
Pins DNS resolution to prevent DNS rebinding attacks.
"""

import ipaddress
import socket
from urllib.parse import urlparse, urlunparse

import requests
from requests.adapters import HTTPAdapter

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


def validate_url(url: str) -> tuple[bool, str, str | None]:
    """Validate a URL is safe to make requests to.

    Returns:
        (is_valid, error_message, resolved_ip) - is_valid is True if the URL
        is safe. resolved_ip is the first resolved IP address (None if DNS
        resolution failed but we want to let the caller handle the error).
    """
    if not url:
        return False, "URL is required", None

    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL format", None

    if parsed.scheme not in ("http", "https"):
        return False, "URL must use http or https", None

    hostname = parsed.hostname
    if not hostname:
        return False, "URL must include a hostname", None

    # Check blocked hostnames
    if hostname.lower() in BLOCKED_HOSTNAMES:
        _logger.warning(f"Blocked SSRF attempt to metadata hostname: {hostname}")
        return False, "Access to this hostname is not allowed", None

    # Resolve hostname and check IP
    resolved_ip = None
    try:
        addr_infos = socket.getaddrinfo(hostname, None)
        for family, _, _, _, sockaddr in addr_infos:
            ip = ipaddress.ip_address(sockaddr[0])
            for blocked in BLOCKED_RANGES:
                if ip in blocked:
                    _logger.warning(f"Blocked SSRF attempt: {hostname} resolves to {ip} (in {blocked})")
                    return False, "Access to this address is not allowed", None
        # Use the first resolved IP for connection pinning
        if addr_infos:
            resolved_ip = addr_infos[0][4][0]
    except socket.gaierror:
        # DNS resolution failed - let the actual request handle this error
        pass
    except Exception as e:
        _logger.debug(f"URL validation DNS check error for {hostname}: {e}")

    return True, "", resolved_ip


class _IPPinningAdapter(HTTPAdapter):
    """HTTPAdapter that pins connections to a specific IP address.

    Replaces the hostname with the resolved IP in the connection pool while
    preserving the original hostname for TLS SNI and certificate validation.
    """

    def __init__(self, resolved_ip, original_hostname, **kwargs):
        self._resolved_ip = resolved_ip
        self._original_hostname = original_hostname
        super().__init__(**kwargs)

    def send(self, request, *args, **kwargs):
        # Replace hostname with resolved IP in the URL for the actual connection
        parsed = urlparse(request.url)
        # Wrap IPv6 addresses in brackets per RFC 2732
        ip = ipaddress.ip_address(self._resolved_ip)
        ip_str = f"[{ip}]" if ip.version == 6 else str(ip)
        # Reconstruct with IP instead of hostname, preserving port if present
        if parsed.port:
            netloc = f"{ip_str}:{parsed.port}"
        else:
            netloc = ip_str
        request.url = urlunparse(parsed._replace(netloc=netloc))

        # Explicitly set Host header to original hostname so virtual hosts and
        # TLS hostname verification use the correct name, not the pinned IP
        request.headers["Host"] = self._original_hostname

        return super().send(request, *args, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        # For HTTPS: set server_hostname so TLS SNI and cert validation
        # use the original hostname, not the IP we're connecting to
        kwargs["server_hostname"] = self._original_hostname
        super().init_poolmanager(*args, **kwargs)


def make_validated_request(url, resolved_ip, method="GET", **kwargs):
    """Make an HTTP request pinned to a pre-resolved IP address.

    This prevents DNS rebinding attacks by ensuring the connection goes to
    the same IP that was validated by validate_url().

    If resolved_ip is None (DNS failed during validation), falls back to
    a normal request and lets requests handle the DNS error.

    Args:
        url: The original URL to request.
        resolved_ip: The IP address from validate_url() to pin the connection to.
        method: HTTP method (default "GET").
        **kwargs: Additional arguments passed to requests.Session.request().

    Returns:
        requests.Response object.
    """
    if resolved_ip is None:
        return requests.request(method, url, **kwargs)

    parsed = urlparse(url)
    original_hostname = parsed.hostname

    session = requests.Session()
    adapter = _IPPinningAdapter(resolved_ip, original_hostname)
    session.mount(f"{parsed.scheme}://", adapter)

    return session.request(method, url, **kwargs)
