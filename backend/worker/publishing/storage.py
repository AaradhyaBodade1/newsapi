from __future__ import annotations

import uuid

from worker.config import get_config
from common.supabase_client import get_supabase


def _sniff_image_type(data: bytes) -> tuple[str, str]:
    """Images now come from several real-world sources (source RSS feeds,
    Unsplash, the branded placeholder) instead of a single AI generator that
    always returned one format, so the extension/content-type must match the
    actual bytes rather than being hardcoded."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png", "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp", "image/webp"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif", "image/gif"
    return "jpg", "image/jpeg"


def upload_image(image_bytes: bytes, article_id: str) -> str:
    """Uploads a generated image to the public `post-images` Supabase Storage
    bucket (create it once, see supabase/README.md) and returns its public URL
    — the website needs a public URL, not raw bytes."""
    config = get_config()
    client = get_supabase()
    ext, content_type = _sniff_image_type(image_bytes)
    path = f"{article_id}/{uuid.uuid4().hex}.{ext}"

    client.storage.from_(config.storage_bucket).upload(
        path, image_bytes, {"content-type": content_type}
    )
    return client.storage.from_(config.storage_bucket).get_public_url(path)
