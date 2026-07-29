from __future__ import annotations

import json

from openai import OpenAI

from worker.ai.prompt_builder import build_user_message, get_system_prompt
from worker.config import get_config
from worker.pipeline.retry import call_with_retry
from common.credentials_store import get_groq_key
from common.schemas import Article, GeneratedContent

# Groq's API is OpenAI-compatible, so the same SDK works pointed at their base_url.
# Free tier, no OpenAI billing involved.
GROQ_BASE_URL = "https://api.groq.com/openai/v1"


def generate_content(article: Article, category_id: str | None, category_name: str | None, source_name: str | None) -> GeneratedContent:
    config = get_config()
    client = OpenAI(api_key=get_groq_key(), base_url=GROQ_BASE_URL)

    system_prompt = get_system_prompt(category_id)
    user_message = build_user_message(article, category_name, source_name)

    def _call():
        response = client.chat.completions.create(
            model=config.text_model,
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

    data = call_with_retry(_call, max_attempts=3, context=f"Groq text generation for '{article.title}'")
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
