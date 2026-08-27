"""
Tests for HTTP Fetch Tool (SSRF prevention & validation) per spec §9.2 & §25.1
"""

import pytest
from app.tools.http_fetch import _is_private_ip, _validate_url


def test_ssrf_blocking():
    # Loopback
    assert _is_private_ip("127.0.0.1") is True
    assert _is_private_ip("localhost") is True
    # Private RFC 1918
    assert _is_private_ip("10.0.0.1") is True
    assert _is_private_ip("192.168.1.1") is True
    assert _is_private_ip("172.16.0.1") is True
    # Public
    assert _is_private_ip("8.8.8.8") is False


def test_url_validation():
    valid, _ = _validate_url("http://127.0.0.1/admin")
    assert valid is False

    valid, _ = _validate_url("ftp://example.com/file")
    assert valid is False

    valid, _ = _validate_url("https://api.github.com/events")
    assert valid is True
