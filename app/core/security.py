"""URL validation, SSRF protection, and input sanitization."""

from __future__ import annotations

import ipaddress
import re
import socket
from urllib.parse import urlparse

from fastapi import HTTPException

MAX_URL_LENGTH = 2048
MAX_SELECTOR_LENGTH = 256
MAX_SELECTORS = 20
MAX_URLS_PER_JOB = 50

# Private/reserved ranges blocked unless ALLOW_PRIVATE_URLS=true
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

_UNSAFE_SELECTOR_PATTERNS = re.compile(
    r"[<>{}]|javascript:|expression\s*\(|url\s*\(",
    re.IGNORECASE,
)


class SecurityError(ValueError):
    """Raised when input fails security validation."""


def validate_url_scheme(url: str) -> None:
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        raise SecurityError(f"Only http and https URLs are allowed, got: {parsed.scheme or 'none'}")
    if not parsed.netloc:
        raise SecurityError("URL must include a hostname")
    if len(url) > MAX_URL_LENGTH:
        raise SecurityError(f"URL exceeds maximum length of {MAX_URL_LENGTH} characters")


def _hostname_resolves_to_private(hostname: str) -> bool:
    """Resolve hostname and check if any resolved IP is in a blocked range."""
    try:
        addr_infos = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        return False

    for info in addr_infos:
        ip_str = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue
        for network in _BLOCKED_NETWORKS:
            if ip in network:
                return True
    return False


def validate_url_ssrf(url: str, *, allow_private: bool = False) -> str:
    """Validate URL and block SSRF to private networks."""
    url = url.strip()
    validate_url_scheme(url)
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        raise SecurityError("Invalid URL hostname")

    if hostname.lower() in ("localhost", "localhost.localdomain"):
        if not allow_private:
            raise SecurityError(
                "SSRF_BLOCKED: localhost URLs are not allowed. "
                "Set ALLOW_PRIVATE_URLS=true to override (not recommended in production)."
            )
        return url

    # Direct IP check
    try:
        ip = ipaddress.ip_address(hostname)
        if not allow_private:
            for network in _BLOCKED_NETWORKS:
                if ip in network:
                    raise SecurityError(
                        "SSRF_BLOCKED: Private or reserved IP addresses are not allowed. "
                        "Set ALLOW_PRIVATE_URLS=true to override."
                    )
    except ValueError:
        # Hostname — resolve and check
        if not allow_private and _hostname_resolves_to_private(hostname):
            raise SecurityError(
                "SSRF_BLOCKED: URL resolves to a private or reserved IP address. "
                "Set ALLOW_PRIVATE_URLS=true to override."
            )

    return url


def validate_css_selector(selector: str) -> str:
    """Sanitize CSS selector to prevent injection."""
    selector = selector.strip()
    if not selector:
        raise SecurityError("Empty CSS selector")
    if len(selector) > MAX_SELECTOR_LENGTH:
        raise SecurityError(f"Selector exceeds maximum length of {MAX_SELECTOR_LENGTH}")
    if _UNSAFE_SELECTOR_PATTERNS.search(selector):
        raise SecurityError("Selector contains disallowed characters or patterns")
    return selector


def validate_selectors(selectors: list[str]) -> list[str]:
    if len(selectors) > MAX_SELECTORS:
        raise SecurityError(f"Maximum {MAX_SELECTORS} selectors allowed")
    return [validate_css_selector(s) for s in selectors if s.strip()]


def validate_urls_list(urls: list[str], *, allow_private: bool = False) -> list[str]:
    if len(urls) > MAX_URLS_PER_JOB:
        raise SecurityError(f"Maximum {MAX_URLS_PER_JOB} URLs allowed per job")
    validated: list[str] = []
    for url in urls:
        cleaned = url.strip()
        if cleaned:
            validated.append(validate_url_ssrf(cleaned, allow_private=allow_private))
    return validated


def http_security_error(exc: SecurityError) -> HTTPException:
    return HTTPException(status_code=422, detail=str(exc))
