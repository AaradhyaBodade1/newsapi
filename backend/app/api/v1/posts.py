from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import AdminUser, get_current_admin
from common.enums import PostStatus
from common.supabase_client import get_supabase

router = APIRouter(prefix="/posts", tags=["posts"], dependencies=[Depends(get_current_admin)])


class PostUpdate(BaseModel):
    headline: str | None = None
    caption: str | None = None
    summary: str | None = None
    cta: str | None = None
    hashtags: list[str] | None = None
    image_prompt: str | None = None


@router.get("")
def list_posts(status: PostStatus | None = None, limit: int = 50, offset: int = 0):
    query = get_supabase().table("generated_posts").select("*, articles(*)", count="exact")
    if status is not None:
        query = query.eq("status", status.value)
    resp = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    return {"items": resp.data, "total": resp.count}


@router.get("/{post_id}")
def get_post(post_id: UUID):
    resp = (
        get_supabase()
        .table("generated_posts")
        .select("*, articles(*), publish_jobs(*)")
        .eq("id", str(post_id))
        .limit(1)
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Post not found")
    return resp.data[0]


@router.patch("/{post_id}")
def update_post(post_id: UUID, payload: PostUpdate):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    resp = get_supabase().table("generated_posts").update(updates).eq("id", str(post_id)).execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Post not found")
    return resp.data[0]


@router.post("/{post_id}/approve")
def approve_post(post_id: UUID, admin: AdminUser = Depends(get_current_admin)):
    updates = {
        "status": PostStatus.APPROVED.value,
        "reviewed_by": admin.id,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }
    resp = get_supabase().table("generated_posts").update(updates).eq("id", str(post_id)).execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Post not found")
    return resp.data[0]


@router.post("/{post_id}/reject")
def reject_post(post_id: UUID, admin: AdminUser = Depends(get_current_admin)):
    updates = {
        "status": PostStatus.REJECTED.value,
        "reviewed_by": admin.id,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }
    resp = get_supabase().table("generated_posts").update(updates).eq("id", str(post_id)).execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Post not found")
    return resp.data[0]
