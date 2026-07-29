from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_admin
from common.supabase_client import get_supabase

router = APIRouter(prefix="/articles", tags=["articles"], dependencies=[Depends(get_current_admin)])


@router.get("")
def list_articles(
    category_id: UUID | None = None,
    status: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    query = get_supabase().table("articles").select("*", count="exact")
    if category_id is not None:
        query = query.eq("category_id", str(category_id))
    if status is not None:
        query = query.eq("status", status)
    if search:
        query = query.ilike("title", f"%{search}%")
    resp = query.order("fetched_at", desc=True).range(offset, offset + limit - 1).execute()
    return {"items": resp.data, "total": resp.count}


@router.get("/{article_id}")
def get_article(article_id: UUID):
    resp = get_supabase().table("articles").select("*").eq("id", str(article_id)).limit(1).execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Article not found")
    return resp.data[0]
