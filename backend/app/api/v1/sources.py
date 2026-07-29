from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import get_current_admin
from common.enums import SourceType
from common.supabase_client import get_supabase

router = APIRouter(prefix="/sources", tags=["sources"], dependencies=[Depends(get_current_admin)])


class SourceCreate(BaseModel):
    name: str
    type: SourceType
    url: str
    category_id: UUID | None = None
    is_active: bool = True
    fetch_interval_minutes: int | None = None
    manual_approval: bool = False


class SourceUpdate(BaseModel):
    name: str | None = None
    type: SourceType | None = None
    url: str | None = None
    category_id: UUID | None = None
    is_active: bool | None = None
    fetch_interval_minutes: int | None = None
    manual_approval: bool | None = None


@router.get("")
def list_sources(category_id: UUID | None = None, is_active: bool | None = None):
    query = get_supabase().table("sources").select("*")
    if category_id is not None:
        query = query.eq("category_id", str(category_id))
    if is_active is not None:
        query = query.eq("is_active", is_active)
    resp = query.order("name").execute()
    return resp.data


@router.post("", status_code=201)
def create_source(payload: SourceCreate):
    body = payload.model_dump(mode="json")
    resp = get_supabase().table("sources").insert(body).execute()
    return resp.data[0]


@router.patch("/{source_id}")
def update_source(source_id: UUID, payload: SourceUpdate):
    updates = {k: v for k, v in payload.model_dump(mode="json").items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    resp = get_supabase().table("sources").update(updates).eq("id", str(source_id)).execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Source not found")
    return resp.data[0]


@router.delete("/{source_id}", status_code=204)
def delete_source(source_id: UUID):
    get_supabase().table("sources").delete().eq("id", str(source_id)).execute()
