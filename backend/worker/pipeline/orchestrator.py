from __future__ import annotations

import logging
from datetime import datetime, timezone

from dateutil import parser as dateutil_parser
from openai import RateLimitError

from worker.ai.image_generator import fetch_source_image, generate_image
from worker.ai.quality_checks import evaluate
from worker.ai.text_generator import generate_content
from worker.db import repositories as repo
from worker.ingestion.pipeline import ingest_new_articles
from worker.notifications.notifier import notify_job_failure
from worker.pipeline.retry import call_with_retry
from worker.publishing.storage import upload_image
from worker.publishing.website_publisher import publish_to_website
from common.enums import PostStatus
from common.schemas import Article
from common.settings_store import get_all_settings

logger = logging.getLogger(__name__)


def run_cycle() -> dict:
    # avoid stale category/source names carrying over between --loop iterations
    repo.get_category_name.cache_clear()
    repo.get_source_name.cache_clear()
    repo.get_source_manual_approval.cache_clear()

    settings = get_all_settings()
    job_run_id = repo.create_job_run()
    counts = {"articles_fetched": 0, "posts_generated": 0, "posts_published": 0, "errors_count": 0}
    logger.info("Job run %s started", job_run_id)

    try:
        inserted = ingest_new_articles()
        counts["articles_fetched"] = len(inserted)
        logger.info("Ingested %s new articles", len(inserted))
    except Exception:
        logger.exception("Ingestion step failed entirely")
        counts["errors_count"] += 1

    max_articles = int(settings["max_articles_per_run"])
    quality_threshold = float(settings["quality_score_threshold"])
    manual_approval_default = bool(settings["manual_approval_default"])

    for article_row in repo.get_articles_to_process(max_articles):
        _process_article(article_row, quality_threshold, manual_approval_default, counts)

    max_retry_attempts = int(settings["max_retry_attempts"])
    for post in repo.get_posts_ready_to_publish():
        _publish_post(post, max_retry_attempts, counts)

    if counts["errors_count"] == 0:
        status = "success"
    elif counts["posts_generated"] > 0 or counts["posts_published"] > 0:
        status = "partial_failure"
    else:
        status = "failed"
    repo.finish_job_run(job_run_id, status, counts, counts)
    logger.info("Job run %s finished: %s", job_run_id, counts)

    if counts["errors_count"] > 0:
        notify_job_failure(
            job_run_id,
            f"Job run {job_run_id} finished with status={status}. Summary: {counts}",
        )

    return counts


def _process_article(article_row: dict, quality_threshold: float, manual_approval_default: bool, counts: dict) -> None:
    article_id = article_row["id"]
    repo.update_article_status(article_id, "processing")
    try:
        published_at = article_row.get("published_at")
        article = Article(
            id=article_id,
            source_id=article_row.get("source_id"),
            category_id=article_row.get("category_id"),
            title=article_row["title"],
            summary=article_row.get("summary"),
            url=article_row["url"],
            published_at=dateutil_parser.parse(published_at) if published_at else None,
            content_hash=article_row["content_hash"],
            image_url=article_row.get("image_url"),
        )
        category_id = article_row.get("category_id")
        category_name = repo.get_category_name(category_id)
        source_name = repo.get_source_name(article_row.get("source_id"))

        generated = generate_content(article, category_id, category_name, source_name)
        quality = evaluate(generated, quality_threshold)

        if not quality.passed:
            repo.insert_generated_post(
                {
                    "article_id": article_id,
                    "headline": generated.headline,
                    "caption": generated.caption,
                    "summary": generated.summary,
                    "cta": generated.cta,
                    "hashtags": generated.hashtags,
                    "image_prompt": generated.image_prompt,
                    "quality_score": generated.quality_score,
                    "profanity_flag": quality.profanity_flag,
                    "status": PostStatus.REJECTED.value,
                }
            )
            repo.update_article_status(article_id, "processed")
            logger.warning("Article %s rejected by quality gate: %s", article_id, quality.reasons)
            counts["errors_count"] += 1
            return

        image_bytes = _get_image_bytes(article.image_url, generated.hashtags, category_name, generated.image_prompt)
        image_url = upload_image(image_bytes, article_id)

        manual_approval = manual_approval_default or repo.get_source_manual_approval(article_row.get("source_id"))
        post_status = PostStatus.PENDING_REVIEW.value if manual_approval else PostStatus.APPROVED.value

        repo.insert_generated_post(
            {
                "article_id": article_id,
                "headline": generated.headline,
                "caption": generated.caption,
                "summary": generated.summary,
                "cta": generated.cta,
                "hashtags": generated.hashtags,
                "image_prompt": generated.image_prompt,
                "image_url": image_url,
                "quality_score": generated.quality_score,
                "profanity_flag": quality.profanity_flag,
                "approval_required": manual_approval,
                "status": post_status,
            }
        )
        repo.update_article_status(article_id, "processed")
        counts["posts_generated"] += 1
    except RateLimitError:
        # Transient and quota-based (e.g. Groq's daily token cap) — leave the
        # article as "new" so it's retried on a later cycle instead of being
        # permanently discarded for a problem that resolves on its own.
        logger.warning("Rate limited processing article %s — left as 'new' to retry later", article_id)
        repo.update_article_status(article_id, "new")
        counts["errors_count"] += 1
    except Exception:
        logger.exception("Failed to process article %s", article_id)
        repo.update_article_status(article_id, "failed")
        counts["errors_count"] += 1


def _get_image_bytes(
    source_image_url: str | None, hashtags: list[str], category_name: str | None, image_prompt: str
) -> bytes:
    """Three-tier fallback: the source publisher's own article image (most
    specific), then a real Unsplash stock photo searched by the story's main
    keyword, then AI generation as a last resort so a post is never left
    with no image at all."""
    if source_image_url:
        try:
            return fetch_source_image(source_image_url)
        except Exception:
            logger.warning("Source image download failed for %s, trying Unsplash next", source_image_url)

    keyword = hashtags[0] if hashtags else (category_name or "news")
    try:
        unsplash_bytes = fetch_unsplash_image(keyword)
        if unsplash_bytes:
            return unsplash_bytes
    except Exception:
        logger.warning("Unsplash search failed for '%s', falling back to AI generation", keyword)

    return generate_image(image_prompt)


def _publish_post(post: dict, max_retry_attempts: int, counts: dict) -> None:
    post_id = post["id"]
    image_url = post.get("image_url")
    if not image_url:
        logger.error("Approved post %s has no image_url, skipping publish", post_id)
        counts["errors_count"] += 1
        return

    platforms = (("website", lambda: publish_to_website(post_id)),)

    all_success = True
    for platform, publish_fn in platforms:
        existing = repo.get_publish_job(post_id, platform)
        if existing and existing["status"] == "success":
            continue

        attempt_count = existing["attempt_count"] if existing else 0
        try:
            external_id = call_with_retry(
                publish_fn,
                max_attempts=max_retry_attempts,
                context=f"publish {platform} for post {post_id}",
            )
            repo.upsert_publish_job(
                generated_post_id=post_id,
                platform=platform,
                status="success",
                attempt_count=attempt_count + 1,
                last_error=None,
                external_post_id=external_id,
                published_at=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as exc:  # noqa: BLE001 - one platform failing must not block the others
            all_success = False
            repo.upsert_publish_job(
                generated_post_id=post_id,
                platform=platform,
                status="failed",
                attempt_count=attempt_count + max_retry_attempts,
                last_error=str(exc)[:500],
                external_post_id=None,
                published_at=None,
            )
            logger.error("Publishing %s failed for post %s: %s", platform, post_id, exc)
            counts["errors_count"] += 1

    if all_success:
        repo.update_generated_post_status(post_id, PostStatus.PUBLISHED.value)
        counts["posts_published"] += 1
