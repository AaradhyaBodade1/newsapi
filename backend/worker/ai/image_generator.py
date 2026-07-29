from __future__ import annotations

import random
import time
from urllib.parse import quote

import httpx

from worker.pipeline.retry import call_with_retry
from common.credentials_store import get_unsplash_key

_UNSPLASH_SEARCH_URL = "https://api.unsplash.com/search/photos"

_SAFETY_SUFFIX = (
    " Photorealistic photograph, natural lighting, real-world detail, DSLR quality, not an "
    "illustration or painting. No readable text or logos, no real identifiable public figures, "
    "safe for work, high quality."
)

# Pollinations.ai: free, no API key required. Returns the generated image
# directly as the response body.
_POLLINATIONS_BASE_URL = "https://image.pollinations.ai/prompt"

# Free-tier rate limit: pace requests so a run of several articles in a row
# doesn't trip a 429, rather than only backing off after already being throttled.
_MIN_SECONDS_BETWEEN_REQUESTS = 3.0
_last_request_at: float = 0.0


def generate_image(image_prompt: str) -> bytes:
    prompt = quote((image_prompt + _SAFETY_SUFFIX)[:4000])

    def _call() -> bytes:
        global _last_request_at
        wait = _MIN_SECONDS_BETWEEN_REQUESTS - (time.monotonic() - _last_request_at)
        if wait > 0:
            time.sleep(wait)
        _last_request_at = time.monotonic()

        # Random seed so a retry (or two articles with a similar prompt) doesn't
        # hit Pollinations' cache and return the same image.
        params = {"width": 1024, "height": 1024, "nologo": "true", "seed": random.randint(0, 2**31)}
        response = httpx.get(f"{_POLLINATIONS_BASE_URL}/{prompt}", params=params, timeout=60)
        response.raise_for_status()
        return response.content

    return call_with_retry(
        _call, max_attempts=4, backoff_base_seconds=4, context="Pollinations image generation"
    )


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
