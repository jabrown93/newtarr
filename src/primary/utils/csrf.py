"""Pure CSRF policy helpers (no Flask imports).

Kept in its own module so the policy can be unit-tested without importing
`web_server`, which touches `/config` at module load.
"""
import os
from urllib.parse import urlparse
from typing import Optional, Set, Tuple

CSRF_SAFE_METHODS = {'GET', 'HEAD', 'OPTIONS', 'TRACE'}

Origin = Tuple[str, str, int]


def normalize_origin(scheme: Optional[str], host_header: Optional[str]) -> Optional[Origin]:
    """Return (scheme, hostname, port) with the default port resolved from the
    scheme. Returns None if the input doesn't parse to a usable origin."""
    if not host_header:
        return None
    scheme = (scheme or 'http').lower()
    parsed = urlparse(f'{scheme}://{host_header}')
    if not parsed.hostname:
        return None
    port = parsed.port
    if port is None:
        port = 443 if scheme == 'https' else 80
    return (scheme, parsed.hostname.lower(), port)


def parse_trusted_origins(raw: Optional[str]) -> Tuple[Set[Origin], Set[str]]:
    """Parse a comma-separated NEWTARR_TRUSTED_ORIGINS value into
    (full_origins, bare_hostnames).

    Entries with a scheme (e.g. https://example.com:8443) match as full
    origins (scheme/host/port). Bare hostnames (example.com) match on
    hostname alone — an explicit operator opt-in for reverse proxies that
    may rewrite scheme or port.
    """
    origins: Set[Origin] = set()
    hostnames: Set[str] = set()
    for item in (raw or '').split(','):
        item = item.strip()
        if not item:
            continue
        if '//' in item:
            parsed = urlparse(item)
            origin = normalize_origin(parsed.scheme, parsed.netloc)
            if origin:
                origins.add(origin)
        else:
            hostnames.add(item.lower())
    return origins, hostnames


def request_allowed(method: str,
                    source_url: Optional[str],
                    expected_origin: Optional[Origin],
                    trusted_origins: Set[Origin],
                    trusted_hostnames: Set[str]) -> bool:
    """Pure CSRF policy check. Returns True if the request should be allowed."""
    if method in CSRF_SAFE_METHODS:
        return True
    if not source_url:
        # No browser-supplied origin — not a CSRF vector (non-browser client).
        return True
    parsed = urlparse(source_url)
    source_origin = normalize_origin(parsed.scheme, parsed.netloc)
    if not source_origin:
        return False
    if expected_origin and source_origin == expected_origin:
        return True
    if source_origin in trusted_origins:
        return True
    if source_origin[1] in trusted_hostnames:
        return True
    return False


# Process-lifetime cache for the env-var parse.
_trusted_cache: Optional[Tuple[Set[Origin], Set[str]]] = None


def trusted_origins_from_env() -> Tuple[Set[Origin], Set[str]]:
    """Cached parse of NEWTARR_TRUSTED_ORIGINS for the current process."""
    global _trusted_cache
    if _trusted_cache is None:
        _trusted_cache = parse_trusted_origins(os.environ.get('NEWTARR_TRUSTED_ORIGINS'))
    return _trusted_cache


def _reset_cache_for_tests() -> None:
    """Test-only: clear the cached env parse so a test can set the env var
    and observe the change."""
    global _trusted_cache
    _trusted_cache = None
