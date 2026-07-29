"""Duplicate-detection hashing, shared so the worker (writes) and backend
(admin search/debug tooling) compute the same hash for the same article.
"""
from __future__ import annotations

import hashlib
import re
from urllib.parse import urlsplit, urlunsplit

_TRACKING_PARAMS_RE = re.compile(r"^(utm_|fbclid|gclid|ref$)", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")


def normalize_url(url: str) -> str:
    """Strip tracking query params and fragments so the same article linked
    with different campaign tags still dedupes to one row."""
    parts = urlsplit(url.strip())
    if parts.query:
        kept = [
            kv
            for kv in parts.query.split("&")
            if kv and not _TRACKING_PARAMS_RE.match(kv.split("=", 1)[0])
        ]
        query = "&".join(kept)
    else:
        query = ""
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), query, ""))


def normalize_title(title: str) -> str:
    return _WHITESPACE_RE.sub(" ", title.strip().lower())


def compute_content_hash(title: str, url: str) -> str:
    normalized = f"{normalize_title(title)}|{normalize_url(url)}"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
