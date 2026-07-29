from __future__ import annotations

from pathlib import Path

import httpx

from worker.pipeline.retry import call_with_retry
from common.credentials_store import get_unsplash_key

_UNSPLASH_SEARCH_URL = "https://api.unsplash.com/search/photos"

# Final fallback when neither the source's own image nor an Unsplash match is
# found — a fixed branded graphic so a post is never left with no image at all.
_PLACEHOLDER_PATH = Path(__file__).resolve().parent.parent / "assets" / "placeholder.jpg"


def get_placeholder_image() -> bytes:
    return _PLACEHOLDER_PATH.read_bytes()


def fetch_source_image(image_url: str) -> bytes:
    """Downloads the source publisher's own article image (extracted at
    ingestion time from the RSS enclosure/media tags or an embedded <img>).
    Preferred over AI generation when the source provides one."""

    def _call() -> bytes:
        response = httpx.get(image_url, timeout=30, headers={"User-Agent": "ArkaNewsBot/1.0"})
        response.raise_for_status()
        return response.content

    return call_with_retry(_call, max_attempts=2, context="source image download")


def fetch_unsplash_image(query: str) -> bytes | None:
    """Searches Unsplash for a real stock photo matching the story's main
    keyword. Returns None (not an exception) when no key is configured or no
    result is found, so the caller can fall through to AI generation —
    this tier is optional, unlike the other two image sources."""
    access_key = get_unsplash_key()
    if not access_key:
        return None

    def _search() -> dict:
        response = httpx.get(
            _UNSPLASH_SEARCH_URL,
            params={"query": query, "per_page": 1, "orientation": "landscape"},
            headers={"Authorization": f"Client-ID {access_key}"},
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    try:
        results = call_with_retry(_search, max_attempts=2, context=f"Unsplash search for '{query}'")["results"]
    except Exception:
        return None
    if not results:
        return None

    image_url = results[0]["urls"]["regular"]

    def _download() -> bytes:
        response = httpx.get(image_url, timeout=30)
        response.raise_for_status()
        return response.content

    return call_with_retry(_download, max_attempts=2, context="Unsplash image download")
