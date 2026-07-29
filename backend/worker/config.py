import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class WorkerConfig:
    supabase_url: str
    supabase_service_role_key: str
    storage_bucket: str
    text_model: str
    gemini_text_model: str
    request_timeout_seconds: float
    loop_interval_minutes: int


@lru_cache
def get_config() -> WorkerConfig:
    missing = [
        name
        for name in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "CREDENTIALS_ENCRYPTION_KEY")
        if not os.environ.get(name)
    ]
    if missing:
        raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")

    return WorkerConfig(
        supabase_url=os.environ["SUPABASE_URL"],
        supabase_service_role_key=os.environ["SUPABASE_SERVICE_ROLE_KEY"],
        storage_bucket=os.environ.get("SUPABASE_STORAGE_BUCKET", "post-images"),
        text_model=os.environ.get("TEXT_MODEL", "llama-3.3-70b-versatile"),
        gemini_text_model=os.environ.get("GEMINI_TEXT_MODEL", "gemini-2.0-flash"),
        request_timeout_seconds=float(os.environ.get("REQUEST_TIMEOUT_SECONDS", "30")),
        loop_interval_minutes=int(os.environ.get("LOOP_INTERVAL_MINUTES", "10")),
    )
