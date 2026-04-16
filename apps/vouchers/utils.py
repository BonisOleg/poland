"""Helpers for voucher media (e.g. import from WooCommerce URLs)."""

from __future__ import annotations

import os
from urllib.parse import unquote, urlparse

import requests


def voucher_image_filename_from_url(url: str, slug: str) -> str:
    """Derive a safe filename from URL path; fallback to ``{slug}.png``."""
    path = unquote(urlparse(url).path)
    base = os.path.basename(path)
    if not base or base in (".", "..") or ".." in base:
        return f"{slug}.png"
    return base


def fetch_url_bytes(url: str, *, timeout: float = 30) -> bytes:
    """GET URL and return response body; raises ``requests.RequestException`` on failure."""
    headers = {"User-Agent": "HypeGlobalImport/1.0 (+https://hypeglobal.pro)"}
    r = requests.get(url, timeout=timeout, headers=headers)
    r.raise_for_status()
    return r.content
