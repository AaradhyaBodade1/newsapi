from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from common.enums import (
    ArticleStatus,
    PostStatus,
    Platform,
    PromptType,
    PublishStatus,
    SourceType,
)


class Category(BaseModel):
    id: UUID
    slug: str
    name: str
    description: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class Source(BaseModel):
    id: UUID
    name: str
    type: SourceType
    url: str
    category_id: Optional[UUID] = None
    is_active: bool = True
    fetch_interval_minutes: Optional[int] = None
    manual_approval: bool = False
    last_fetched_at: Optional[datetime] = None
    last_error: Optional[str] = None


class Article(BaseModel):
    id: Optional[UUID] = None
    source_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    title: str
    summary: Optional[str] = None
    raw_excerpt: Optional[str] = None
    url: str
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    content_hash: str
    status: ArticleStatus = ArticleStatus.NEW
    image_url: Optional[str] = None


class AIPrompt(BaseModel):
    id: UUID
    name: str
    category_id: Optional[UUID] = None
    prompt_type: PromptType
    template: str
    is_active: bool = True


class GeneratedContent(BaseModel):
    """Structured output the AI text generator must produce for one article."""

    headline: str
    caption: str
    summary: str
    cta: str
    hashtags: list[str] = Field(default_factory=list)
    image_prompt: str
    quality_score: float = 0.0
    is_india_relevant: bool = True


class GeneratedPost(BaseModel):
    id: Optional[UUID] = None
    article_id: UUID
    headline: Optional[str] = None
    caption: Optional[str] = None
    summary: Optional[str] = None
    cta: Optional[str] = None
    hashtags: list[str] = Field(default_factory=list)
    image_prompt: Optional[str] = None
    image_url: Optional[str] = None
    quality_score: Optional[float] = None
    profanity_flag: bool = False
    approval_required: bool = False
    status: PostStatus = PostStatus.DRAFT


class PublishJob(BaseModel):
    id: Optional[UUID] = None
    generated_post_id: UUID
    platform: Platform
    external_post_id: Optional[str] = None
    status: PublishStatus = PublishStatus.PENDING
    attempt_count: int = 0
    last_error: Optional[str] = None
    published_at: Optional[datetime] = None
