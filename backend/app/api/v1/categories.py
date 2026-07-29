from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import get_current_admin
from common.supabase_client import get_supabase

router = APIRouter(prefix="/categories", tags=["categories"], dependencies=[Depends(get_current_admin)])


class CategoryCreate(BaseModel):
    slug: str
    name: str
    description: str | None = None
    sort_order: int = 0
    is_active: bool = True


class CategoryUpdate(BaseModel):
    slug: str | None = None
    name: str | None = None
    description: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


@router.get("")
def list_categories():
    resp = get_supabase().table("categories").select("*").order("sort_order").execute()
    return resp.data


@router.post("", status_code=201)
def create_category(payload: CategoryCreate):
    resp = get_supabase().table("categories").insert(payload.model_dump()).execute()
    return resp.data[0]


@router.patch("/{category_id}")
def update_category(category_id: UUID, payload: CategoryUpdate):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    resp = get_supabase().table("categories").update(updates).eq("id", str(category_id)).execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Category not found")
    return resp.data[0]


@router.delete("/{category_id}", status_code=204)
def delete_category(category_id: UUID):
    get_supabase().table("categories").delete().eq("id", str(category_id)).execute()
