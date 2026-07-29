"""Generic fetcher for `sources.type = 'api'`.

Since public news APIs vary widely in shape, this expects the endpoint to
return a JSON array (or an object with an "articles"/"items"/"results" list)
of objects containing at least a title and a url, with optional summary/
description, author, and a published-date field. This covers common APIs
(NewsAPI-style, most CMS "latest articles" endpoints) without hardcoding a
single vendor. If a source needs bespoke mapping, add a small transform here
keyed off `source["name"]`.
"""
from __future__ import annotations

from datetime import datetime

import httpx
from dateutil import parser as dateutil_parser

from common.dedupe import compute_content_hash
from common.schemas import Article

_LIST_KEYS = ("articles", "items", "results", "data")
_TITLE_KEYS = ("title", "headline", "name")
_URL_KEYS = ("url", "link", "permalink")
_SUMMARY_KEYS = ("summary", "description", "excerpt", "content")
_AUTHOR_KEYS = ("author", "byline", "creator")
_DATE_KEYS = ("published_at", "publishedAt", "pubDate", "date", "created_at")
_IMAGE_KEYS = ("image_url", "urlToImage", "image", "thumbnail", "imageUrl", "og_image")


def fetch_api(source: dict, timeout_seconds: float = 30) -> list[Article]:
    resp = httpx.get(source["url"], timeout=timeout_seconds, headers={"User-Agent": "NewsPlatformBot/1.0"})
    resp.raise_for_status()
    payload = resp.json()

    items = payload if isinstance(payload, list) else _find_list(payload)
    if items is None:
        raise RuntimeError(f"Could not find an article list in API response from {source['url']}")

    articles: list[Article] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        title = _first(item, _TITLE_KEYS)
        url = _first(item, _URL_KEYS)
        if not title or not url:
            continue

        articles.append(
            Article(
                source_id=source["id"],
                category_id=source.get("category_id"),
                title=str(title).strip(),
                summary=_clean(_first(item, _SUMMARY_KEYS)),
                raw_excerpt=_clean(_first(item, _SUMMARY_KEYS)),
                url=str(url).strip(),
                author=_clean(_first(item, _AUTHOR_KEYS)),
                published_at=_parse_date(_first(item, _DATE_KEYS)),
                content_hash=compute_content_hash(str(title), str(url)),
                image_url=_image_url(item),
            )
        )
    return articles


def _find_list(payload: dict) -> list | None:
    for key in _LIST_KEYS:
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return None


def _first(item: dict, keys: tuple[str, ...]) -> str | None:
    for key in keys:
        if item.get(key):
            return item[key]
    return None


def _clean(value) -> str | None:
    return str(value).strip() if value else None


def _image_url(item: dict) -> str | None:
    for key in _IMAGE_KEYS:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict) and isinstance(value.get("url"), str):
            return value["url"].strip()
    return None


def _parse_date(value) -> datetime | None:
    if not value:
        return None
    try:
        return dateutil_parser.parse(str(value))
    except (ValueError, OverflowError):
        return None
