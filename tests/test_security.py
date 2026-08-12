"""Security validation tests."""

import pytest

from app.core.security import SecurityError, validate_css_selector, validate_url_ssrf


def test_block_localhost():
    with pytest.raises(SecurityError, match="localhost"):
        validate_url_ssrf("http://localhost:8000/api/health")


def test_block_private_ip():
    with pytest.raises(SecurityError, match="SSRF_BLOCKED"):
        validate_url_ssrf("http://192.168.1.1/admin")


def test_allow_private_when_enabled():
    url = validate_url_ssrf("http://127.0.0.1:8000", allow_private=True)
    assert url == "http://127.0.0.1:8000"


def test_block_file_scheme():
    with pytest.raises(SecurityError, match="Only http and https"):
        validate_url_ssrf("file:///etc/passwd")


def test_block_unsafe_selector():
    with pytest.raises(SecurityError):
        validate_css_selector("div<script>")


def test_valid_selector():
    assert validate_css_selector(".price_color") == ".price_color"


def test_ssrf_blocks_127_range():
    with pytest.raises(SecurityError):
        validate_url_ssrf("http://127.0.0.1/secret")
