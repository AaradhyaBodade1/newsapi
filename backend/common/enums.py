from enum import Enum


class SourceType(str, Enum):
    RSS = "rss"
    API = "api"


class ArticleStatus(str, Enum):
    NEW = "new"
    PROCESSING = "processing"
    PROCESSED = "processed"
    SKIPPED = "skipped"
    FAILED = "failed"


class PromptType(str, Enum):
    MASTER = "master"
    HEADLINE = "headline"
    CAPTION = "caption"
    SUMMARY = "summary"
    CTA = "cta"
    HASHTAGS = "hashtags"
    IMAGE_PROMPT = "image_prompt"


class PostStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    FAILED = "failed"


class Platform(str, Enum):
    WEBSITE = "website"


class PublishStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class CredentialProvider(str, Enum):
    GROQ = "groq"
    GEMINI = "gemini"
    UNSPLASH = "unsplash"
    SMTP = "smtp"
    WEBHOOK = "webhook"


class JobRunStatus(str, Enum):
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL_FAILURE = "partial_failure"
    FAILED = "failed"
