from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

from common.supabase_client import get_supabase


def create_job_run() -> str:
    resp = get_supabase().table("job_runs").insert({"status": "running"}).execute()
    return resp.data[0]["id"]


def finish_job_run(job_run_id: str, status: str, counts: dict[str, int], summary: dict[str, Any]) -> None:
    get_supabase().table("job_runs").update(
        {
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "articles_fetched": counts.get("articles_fetched", 0),
            "posts_generated": counts.get("posts_generated", 0),
            "posts_published": counts.get("posts_published", 0),
            "errors_count": counts.get("errors_count", 0),
            "summary": summary,
        }
    ).eq("id", job_run_id).execute()


def update_article_status(article_id: str, status: str) -> None:
    get_supabase().table("articles").update({"status": status}).eq("id", article_id).execute()


def get_articles_to_process(limit: int) -> list[dict]:
    resp = (
        get_supabase()
        .table("articles")
        .select("*")
        .eq("status", "new")
        .order("published_at", desc=True, nullsfirst=False)
        .limit(limit)
        .execute()
    )
    return resp.data or []


@lru_cache(maxsize=64)
def get_category_name(category_id: str | None) -> str | None:
    if not category_id:
        return None
    resp = get_supabase().table("categories").select("name").eq("id", category_id).limit(1).execute()
    return resp.data[0]["name"] if resp.data else None


@lru_cache(maxsize=64)
def get_source_name(source_id: str | None) -> str | None:
    if not source_id:
        return None
    resp = get_supabase().table("sources").select("name").eq("id", source_id).limit(1).execute()
    return resp.data[0]["name"] if resp.data else None


@lru_cache(maxsize=64)
def get_source_manual_approval(source_id: str | None) -> bool:
    if not source_id:
        return False
    resp = get_supabase().table("sources").select("manual_approval").eq("id", source_id).limit(1).execute()
    return bool(resp.data[0]["manual_approval"]) if resp.data else False


def insert_generated_post(post: dict) -> dict:
    resp = get_supabase().table("generated_posts").insert(post).execute()
    return resp.data[0]


def update_generated_post_status(post_id: str, status: str) -> None:
    get_supabase().table("generated_posts").update({"status": status}).eq("id", post_id).execute()


def get_posts_ready_to_publish() -> list[dict]:
    """Posts approved (auto or by an admin) that aren't fully published yet.
    Includes posts approved in a *previous* cycle via the review queue, so
    manual approval doesn't require the admin to trigger publishing too."""
    resp = (
        get_supabase()
        .table("generated_posts")
        .select("*, articles(*)")
        .eq("status", "approved")
        .execute()
    )
    return resp.data or []


def get_publish_job(generated_post_id: str, platform: str) -> dict | None:
    resp = (
        get_supabase()
        .table("publish_jobs")
        .select("*")
        .eq("generated_post_id", generated_post_id)
        .eq("platform", platform)
        .limit(1)
        .execute()
    )
    return resp.data[0] if resp.data else None


def upsert_publish_job(
    *,
    generated_post_id: str,
    platform: str,
    status: str,
    attempt_count: int,
    last_error: str | None,
    external_post_id: str | None,
    published_at: str | None,
) -> None:
    existing = get_publish_job(generated_post_id, platform)
    payload = {
        "generated_post_id": generated_post_id,
        "platform": platform,
        "status": status,
        "attempt_count": attempt_count,
        "last_error": last_error,
        "external_post_id": external_post_id,
        "published_at": published_at,
    }
    client = get_supabase()
    if existing:
        client.table("publish_jobs").update(payload).eq("id", existing["id"]).execute()
    else:
        client.table("publish_jobs").insert(payload).execute()
