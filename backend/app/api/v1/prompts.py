from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import get_current_admin
from common.enums import PromptType
from common.supabase_client import get_supabase

router = APIRouter(prefix="/prompts", tags=["prompts"], dependencies=[Depends(get_current_admin)])


class PromptCreate(BaseModel):
    name: str
    category_id: UUID | None = None
    prompt_type: PromptType
    template: str
    is_active: bool = True


class PromptUpdate(BaseModel):
    name: str | None = None
    category_id: UUID | None = None
    prompt_type: PromptType | None = None
    template: str | None = None
    is_active: bool | None = None


@router.get("")
def list_prompts(category_id: UUID | None = None):
    query = get_supabase().table("ai_prompts").select("*")
    if category_id is not None:
        query = query.eq("category_id", str(category_id))
    resp = query.order("created_at", desc=True).execute()
    return resp.data


@router.post("", status_code=201)
def create_prompt(payload: PromptCreate):
    resp = get_supabase().table("ai_prompts").insert(payload.model_dump(mode="json")).execute()
    return resp.data[0]


@router.patch("/{prompt_id}")
def update_prompt(prompt_id: UUID, payload: PromptUpdate):
    updates = {k: v for k, v in payload.model_dump(mode="json").items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    resp = get_supabase().table("ai_prompts").update(updates).eq("id", str(prompt_id)).execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return resp.data[0]


@router.delete("/{prompt_id}", status_code=204)
def delete_prompt(prompt_id: UUID):
    get_supabase().table("ai_prompts").delete().eq("id", str(prompt_id)).execute()
