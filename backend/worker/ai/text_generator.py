from __future__ import annotations

import json
import logging

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
    except RateLimitError:
        gemini_key = get_gemini_key()
        if not gemini_key:
            raise
        logger.warning("Groq rate-limited generating '%s' — falling back to Gemini", article.title)
        gemini_client = OpenAI(api_key=gemini_key, base_url=GEMINI_BASE_URL)
        data = call_with_retry(
            lambda: _call_model(gemini_client, config.gemini_text_model, system_prompt, user_message),
            max_attempts=3,
            context=f"Gemini fallback text generation for '{article.title}'",
        )

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
