from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.security import get_current_admin
from common.enums import CredentialProvider
from common.credentials_store import set_credential
from common.supabase_client import get_supabase

router = APIRouter(prefix="/credentials", tags=["credentials"], dependencies=[Depends(get_current_admin)])


class CredentialWrite(BaseModel):
    provider: CredentialProvider
    key_name: str
    value: str


@router.get("")
def list_credentials():
    """Lists which credentials are configured WITHOUT exposing their values."""
    resp = get_supabase().table("credentials").select("provider, key_name, updated_at").execute()
    return resp.data


@router.put("", status_code=204)
def upsert_credential(payload: CredentialWrite):
    set_credential(payload.provider, payload.key_name, payload.value)


@router.delete("/{provider}/{key_name}", status_code=204)
def delete_credential(provider: str, key_name: str):
    get_supabase().table("credentials").delete().eq("provider", provider).eq("key_name", key_name).execute()
