from __future__ import annotations

from common.schemas import Article
from common.supabase_client import get_supabase

_FALLBACK_TEMPLATE = (
    "You are a professional editor for Arka News, an Indian news website. You will be given a "
    "news article's title, summary, source, category, and URL. Arka News only publishes stories "
    "that are about India, or that have a clear, explainable impact/relevance on India or "
    "Indians (e.g. global markets moving Indian stocks, foreign policy involving India, an "
    "international sports event India is competing in). If the article has no such connection to "
    "India, do not force one — honestly report it as not relevant instead of inventing a link. "
    "Write ENTIRELY ORIGINAL content in a clear, professional journalistic tone that accurately "
    "captures the key facts without copying any sentence from the source, and without "
    "fabricating facts not present in the input. Do not use emojis or clickbait phrasing "
    "anywhere in the output. The caption is a single crisp, tightly-written paragraph of about "
    "10 lines (roughly 120-160 words) — not a bullet list, not separated by newlines, no filler "
    "sentences or padding, every sentence carrying real information. The image_prompt must "
    "describe a photorealistic photograph (natural lighting, real-world detail, DSLR-quality), "
    "never an illustration, cartoon, or painting. Return strict JSON with these keys: headline, "
    "caption, summary, cta, hashtags (array of strings, no # symbol), image_prompt, quality_score "
    "(0-1 float), is_india_relevant (boolean, true only if the story is about India or clearly "
    "affects India)."
)

_OUTPUT_CONTRACT = (
    "\n\nRespond with a single JSON object and nothing else, matching exactly this shape:\n"
    '{"headline": string, "caption": string, "summary": string, '
    '"cta": string, "hashtags": string[], "image_prompt": string, "quality_score": number, '
    '"is_india_relevant": boolean}'
)


def get_system_prompt(category_id: str | None) -> str:
    """Prefers an active category-specific 'master' prompt, falling back to
    the global one (category_id IS NULL), then to a hardcoded fallback so a
    misconfigured/empty ai_prompts table never blocks the pipeline."""
    client = get_supabase()
    query = client.table("ai_prompts").select("template, category_id").eq("prompt_type", "master").eq("is_active", True)
    resp = query.execute()
    rows = resp.data or []

    category_specific = [r for r in rows if r.get("category_id") == category_id]
    global_rows = [r for r in rows if r.get("category_id") is None]

    if category_specific:
        template = category_specific[0]["template"]
    elif global_rows:
        template = global_rows[0]["template"]
    else:
        template = _FALLBACK_TEMPLATE

    return template + _OUTPUT_CONTRACT


def build_user_message(article: Article, category_name: str | None, source_name: str | None) -> str:
    return (
        f"Category: {category_name or 'General'}\n"
        f"Source: {source_name or 'Unknown'}\n"
        f"Title: {article.title}\n"
        f"Summary/excerpt: {article.summary or 'N/A'}\n"
        f"Published: {article.published_at.isoformat() if article.published_at else 'unknown'}\n"
        f"Source URL (for reference only, do not copy its wording): {article.url}"
    )
