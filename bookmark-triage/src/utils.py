"""Shared utility functions."""

from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlparse


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_url(raw_url: str) -> str:
    value = (raw_url or "").strip()
    if not value:
        return ""
    if not value.startswith(("http://", "https://")):
        value = "https://" + value
    return value


def extract_domain(url: str) -> str:
    try:
        parsed = urlparse(url)
    except ValueError:
        return ""
    domain = (parsed.netloc or "").lower().strip()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if not (parsed.scheme and parsed.netloc):
        return False
    host = parsed.netloc
    if any(ch.isspace() for ch in host):
        return False
    return "." in host or host.startswith("localhost")
