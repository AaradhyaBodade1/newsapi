from fastapi import APIRouter, Depends

from app.core.security import get_current_admin
from common.supabase_client import get_supabase

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(get_current_admin)])


@router.get("/stats")
def get_stats():
    client = get_supabase()

    def count(table: str, **filters) -> int:
        query = client.table(table).select("id", count="exact")
        for k, v in filters.items():
            query = query.eq(k, v)
        return query.execute().count or 0

    return {
        "articles_total": count("articles"),
        "articles_new": count("articles", status="new"),
        "posts_pending_review": count("generated_posts", status="pending_review"),
        "posts_published": count("generated_posts", status="published"),
        "posts_failed": count("generated_posts", status="failed"),
        "publish_jobs_failed": count("publish_jobs", status="failed"),
        "sources_active": count("sources", is_active=True),
    }


@router.get("/job-runs")
def list_job_runs(limit: int = 20, offset: int = 0):
    resp = (
        get_supabase()
        .table("job_runs")
        .select("*", count="exact")
        .order("started_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return {"items": resp.data, "total": resp.count}


@router.get("/notifications")
def list_notifications(limit: int = 20, offset: int = 0):
    resp = (
        get_supabase()
        .table("notification_logs")
        .select("*", count="exact")
        .order("sent_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return {"items": resp.data, "total": resp.count}
