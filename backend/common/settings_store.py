"""Typed access to the `settings` key/value table.

Read fresh at the start of every worker cycle (and by the backend admin API)
so changes made from the dashboard take effect without a redeploy.
"""
from __future__ import annotations

from typing import Any

from common.supabase_client import get_supabase

DEFAULTS: dict[str, Any] = {
    "posting_frequency_minutes": 10,
    "manual_approval_default": False,
    "max_retry_attempts": 3,
    "max_articles_per_run": 20,
    "quality_score_threshold": 0.6,
    "notification_email": "",
    "notification_webhook_url": "",
}


def get_all_settings() -> dict[str, Any]:
    client = get_supabase()
    resp = client.table("settings").select("key, value").execute()
    values = {row["key"]: row["value"] for row in resp.data or []}
    return {**DEFAULTS, **values}


def get_setting(key: str) -> Any:
    if key not in DEFAULTS:
        raise KeyError(f"Unknown setting key: {key}")
    client = get_supabase()
    resp = client.table("settings").select("value").eq("key", key).limit(1).execute()
    if resp.data:
        return resp.data[0]["value"]
    return DEFAULTS[key]


def set_setting(key: str, value: Any, description: str | None = None) -> None:
    client = get_supabase()
    payload: dict[str, Any] = {"key": key, "value": value}
    if description is not None:
        payload["description"] = description
    client.table("settings").upsert(payload, on_conflict="key").execute()
