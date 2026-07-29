from __future__ import annotations

import uuid

from worker.config import get_config
from common.supabase_client import get_supabase


def upload_image(image_bytes: bytes, article_id: str) -> str:
    """Uploads a generated image to the public `post-images` Supabase Storage
    bucket (create it once, see supabase/README.md) and returns its public URL
    — the website needs a public URL, not raw bytes."""
    config = get_config()
    client = get_supabase()
    path = f"{article_id}/{uuid.uuid4().hex}.png"

    client.storage.from_(config.storage_bucket).upload(
        path, image_bytes, {"content-type": "image/png"}
    )
    return client.storage.from_(config.storage_bucket).get_public_url(path)
