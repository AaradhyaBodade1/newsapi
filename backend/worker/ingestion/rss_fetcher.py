from __future__ import annotations

import re
from datetime import datetime, timezone
from time import mktime

import feedparser

from common.dedupe import compute_content_hash
from common.schemas import Article

_IMG_SRC_RE = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)


def fetch_rss(source: dict, timeout_seconds: float = 30) -> list[Article]:
    """Fetch and normalize entries from an RSS/Atom feed. Never raises on a
    single malformed entry — that entry is just skipped."""
    parsed = feedparser.parse(source["url"], request_headers={"User-Agent": "NewsPlatformBot/1.0"})
    if parsed.bozo and not parsed.entries:
        raise RuntimeError(f"Failed to parse RSS feed {source['url']}: {parsed.bozo_exception}")

    articles: list[Article] = []
    for entry in parsed.entries:
        title = getattr(entry, "title", None)
        link = getattr(entry, "link", None)
        if not title or not link:
            continue

        summary = getattr(entry, "summary", None) or getattr(entry, "description", None)
        author = getattr(entry, "author", None)
        published_at = _extract_published(entry)

        articles.append(
            Article(
                source_id=source["id"],
                category_id=source.get("category_id"),
                title=title.strip(),
                summary=summary.strip() if summary else None,
                raw_excerpt=summary.strip() if summary else None,
                url=link.strip(),
                author=author,
                published_at=published_at,
                content_hash=compute_content_hash(title, link),
                image_url=_extract_image(entry, summary),
            )
        )
    return articles


def _extract_published(entry) -> datetime | None:
    for field in ("published_parsed", "updated_parsed"):
        value = getattr(entry, field, None)
        if value:
            return datetime.fromtimestamp(mktime(value), tz=timezone.utc)
    return None


def _extract_image(entry, summary: str | None) -> str | None:
    """Most feeds don't embed an image at all — this is best-effort across
    the handful of mechanisms publishers actually use, not guaranteed to
    find one."""
    for enclosure in getattr(entry, "enclosures", None) or []:
        href = enclosure.get("href") or enclosure.get("url")
        enc_type = enclosure.get("type", "")
        if href and (not enc_type or enc_type.startswith("image/")):
            return href

    media_content = getattr(entry, "media_content", None) or []
    for media in media_content:
        url = media.get("url")
        medium = media.get("medium", "")
        if url and (medium == "image" or not medium):
            return url

    media_thumbnail = getattr(entry, "media_thumbnail", None) or []
    if media_thumbnail and media_thumbnail[0].get("url"):
        return media_thumbnail[0]["url"]

    if summary:
        match = _IMG_SRC_RE.search(summary)
        if match:
            return match.group(1)

    return None
