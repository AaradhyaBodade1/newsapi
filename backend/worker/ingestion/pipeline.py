from __future__ import annotations

import logging
from datetime import datetime, timezone

from worker.ingestion.api_fetcher import fetch_api
from worker.ingestion.rss_fetcher import fetch_rss
from worker.pipeline.retry import call_with_retry
from common.enums import SourceType
from common.schemas import Article
from common.supabase_client import get_supabase

logger = logging.getLogger(__name__)


def ingest_new_articles(timeout_seconds: float = 30) -> list[dict]:
    """Fetches every active source, dedupes against existing content_hash
    values, inserts genuinely new articles, and returns the inserted rows.
    A single source failing (bad feed URL, timeout, etc.) is logged and
    recorded on the source row — it never aborts the whole ingest pass.
    """
    client = get_supabase()
    sources_resp = client.table("sources").select("*").eq("is_active", True).execute()
    sources = sources_resp.data or []

    fetched: list[Article] = []
    for source in sources:
        try:
            items = call_with_retry(
                lambda s=source: (
                    fetch_rss(s, timeout_seconds) if s["type"] == SourceType.RSS.value else fetch_api(s, timeout_seconds)
                ),
                max_attempts=3,
                context=f"fetch source {source['name']}",
            )
            fetched.extend(items)
            client.table("sources").update(
                {"last_fetched_at": datetime.now(timezone.utc).isoformat(), "last_error": None}
            ).eq("id", source["id"]).execute()
            logger.info("Fetched %s items from %s", len(items), source["name"])
        except Exception as exc:  # noqa: BLE001 - one bad source must not kill the run
            logger.error("Failed to fetch source %s: %s", source["name"], exc)
            client.table("sources").update({"last_error": str(exc)[:500]}).eq("id", source["id"]).execute()

    if not fetched:
        return []

    # Batched: a single .in_() query with hundreds of SHA-256 hashes can exceed the
    # request's URL length limit and get rejected outright.
    hashes = [a.content_hash for a in fetched]
    existing_hashes: set[str] = set()
    batch_size = 100
    for i in range(0, len(hashes), batch_size):
        batch = hashes[i : i + batch_size]
        existing_resp = client.table("articles").select("content_hash").in_("content_hash", batch).execute()
        existing_hashes.update(row["content_hash"] for row in (existing_resp.data or []))

    new_articles = [a for a in fetched if a.content_hash not in existing_hashes]
    if not new_articles:
        return []

    # de-dupe within this same batch too (same story from two feeds in one run)
    seen: set[str] = set()
    deduped: list[Article] = []
    for article in new_articles:
        if article.content_hash in seen:
            continue
        seen.add(article.content_hash)
        deduped.append(article)

    rows = [
        {
            "source_id": str(a.source_id) if a.source_id else None,
            "category_id": str(a.category_id) if a.category_id else None,
            "title": a.title,
            "summary": a.summary,
            "raw_excerpt": a.raw_excerpt,
            "url": a.url,
            "author": a.author,
            "published_at": a.published_at.isoformat() if a.published_at else None,
            "content_hash": a.content_hash,
            "image_url": a.image_url,
            "status": "new",
        }
        for a in deduped
    ]

    # Supabase upsert on the unique content_hash constraint guards against a
    # race with another concurrent run inserting the same story first.
    insert_resp = client.table("articles").upsert(rows, on_conflict="content_hash", ignore_duplicates=True).execute()
    return insert_resp.data or []
