from __future__ import annotations

import json
import logging
import re

from openai import OpenAI, RateLimitError

from worker.ai.prompt_builder import build_user_message, get_system_prompt
from worker.config import get_config
from worker.pipeline.retry import call_with_retry
from common.credentials_store import get_gemini_key, get_groq_key
from common.schemas import Article, GeneratedContent

logger = logging.getLogger(__name__)

# Groq and Gemini both expose OpenAI-compatible endpoints, so the same SDK
# works pointed at either base_url. Groq is primary; Gemini is an optional
# same-day fallback for when Groq's free-tier 100k-tokens/day cap is hit,
# so a busy day doesn't stall generation until the cap resets.
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

_WHITESPACE_RE = re.compile(r"\s+")


def _call_model(client: OpenAI, model: str, system_prompt: str, user_message: str) -> dict:
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        temperature=0.7,
        max_tokens=1500,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    raw = response.choices[0].message.content
    return json.loads(raw)


def _to_generated_content(data: dict) -> GeneratedContent:
    return GeneratedContent(
        headline=data["headline"],
        caption=data["caption"],
        summary=data["summary"],
        cta=data["cta"],
        hashtags=[h.lstrip("#") for h in data.get("hashtags", [])],
        image_prompt=data["image_prompt"],
        quality_score=float(data.get("quality_score", 0.5)),
        is_india_relevant=bool(data.get("is_india_relevant", True)),
    )


def _build_source_fallback(article: Article, category_name: str | None) -> GeneratedContent:
    """Last-resort content tier for when both Groq and Gemini are rate-limited:
    reformats the source publisher's own title/summary into a post instead of
    leaving the article stuck until quota resets. Never includes the source
    URL — same as every other content path on this site."""
    raw_text = (article.summary or article.raw_excerpt or "").strip()
    paragraph = _WHITESPACE_RE.sub(" ", raw_text).strip()
    if len(paragraph) < 40:
        paragraph = _WHITESPACE_RE.sub(" ", f"{article.title}. {paragraph}").strip()

    hashtags = ["IndiaNews"]
    if category_name:
        tag = re.sub(r"[^A-Za-z0-9]", "", category_name)
        if tag:
            hashtags.insert(0, tag)

    return GeneratedContent(
        headline=article.title[:150],
        caption=paragraph[:200] if len(paragraph) >= 10 else f"{article.title[:190]}.",
        summary=paragraph[:900],
        cta="Read more India news on Arka News",
        hashtags=hashtags,
        image_prompt=f"{category_name or 'India'} news",
        quality_score=1.0,
        is_india_relevant=True,
    )


def generate_content(article: Article, category_id: str | None, category_name: str | None, source_name: str | None) -> GeneratedContent:
    config = get_config()
    system_prompt = get_system_prompt(category_id)
    user_message = build_user_message(article, category_name, source_name)

    groq_client = OpenAI(api_key=get_groq_key(), base_url=GROQ_BASE_URL)
    try:
        data = call_with_retry(
            lambda: _call_model(groq_client, config.text_model, system_prompt, user_message),
            max_attempts=3,
            context=f"Groq text generation for '{article.title}'",
        )
        return _to_generated_content(data)
    except RateLimitError:
        logger.warning("Groq rate-limited generating '%s' — trying Gemini next", article.title)

    gemini_key = get_gemini_key()
    if gemini_key:
        try:
            gemini_client = OpenAI(api_key=gemini_key, base_url=GEMINI_BASE_URL)
            data = call_with_retry(
                lambda: _call_model(gemini_client, config.gemini_text_model, system_prompt, user_message),
                max_attempts=3,
                context=f"Gemini fallback text generation for '{article.title}'",
            )
            return _to_generated_content(data)
        except RateLimitError:
            logger.warning("Gemini also rate-limited generating '%s' — falling back to source content", article.title)
    else:
        logger.warning("No Gemini key configured — falling back to source content for '%s'", article.title)

    return _build_source_fallback(article, category_name)
