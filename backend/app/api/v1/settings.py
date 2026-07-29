from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import get_current_admin
from common.settings_store import DEFAULTS, get_all_settings, set_setting

router = APIRouter(prefix="/settings", tags=["settings"], dependencies=[Depends(get_current_admin)])


class SettingUpdate(BaseModel):
    value: Any
    description: str | None = None


@router.get("")
def read_settings():
    return get_all_settings()


@router.put("/{key}")
def update_setting(key: str, payload: SettingUpdate):
    if key not in DEFAULTS:
        raise HTTPException(status_code=400, detail=f"Unknown setting key. Valid keys: {sorted(DEFAULTS)}")
    set_setting(key, payload.value, payload.description)
    return {"key": key, "value": payload.value}
