"""Typed access to the `credentials` table (encrypted API keys/tokens).

Falls back to environment variables when a credential hasn't been configured
from the admin dashboard yet — this keeps local dev simple (just fill in
.env) while letting production be fully dashboard-managed.
"""
from __future__ import annotations

import os

from common.enums import CredentialProvider
from common.security import decrypt_value, encrypt_value
from common.supabase_client import get_supabase

# Maps (provider, key_name) -> fallback env var name
_ENV_FALLBACKS: dict[tuple[str, str], str] = {
    (CredentialProvider.GROQ, "api_key"): "GROQ_API_KEY",
    (CredentialProvider.GEMINI, "api_key"): "GEMINI_API_KEY",
    (CredentialProvider.UNSPLASH, "access_key"): "UNSPLASH_ACCESS_KEY",
    (CredentialProvider.SMTP, "host"): "SMTP_HOST",
    (CredentialProvider.SMTP, "port"): "SMTP_PORT",
    (CredentialProvider.SMTP, "username"): "SMTP_USERNAME",
    (CredentialProvider.SMTP, "password"): "SMTP_PASSWORD",
    (CredentialProvider.WEBHOOK, "url"): "NOTIFICATION_WEBHOOK_URL",
}


def get_credential(provider: str, key_name: str) -> str | None:
    # CredentialProvider is a (str, Enum): equality/hashing against plain strings
    # works fine, but postgrest's query-string builder renders it as
    # "CredentialProvider.GROQ" instead of "groq" unless coerced explicitly here.
    provider_value = provider.value if isinstance(provider, CredentialProvider) else provider

    client = get_supabase()
    resp = (
        client.table("credentials")
        .select("encrypted_value")
        .eq("provider", provider_value)
        .eq("key_name", key_name)
        .limit(1)
        .execute()
    )
    if resp.data:
        return decrypt_value(resp.data[0]["encrypted_value"])

    env_var = _ENV_FALLBACKS.get((provider, key_name))
    if env_var:
        return os.environ.get(env_var)
    return None


def set_credential(provider: str, key_name: str, plaintext_value: str) -> None:
    provider_value = provider.value if isinstance(provider, CredentialProvider) else provider
    client = get_supabase()
    payload = {
        "provider": provider_value,
        "key_name": key_name,
        "encrypted_value": encrypt_value(plaintext_value),
    }
    client.table("credentials").upsert(payload, on_conflict="provider,key_name").execute()


def get_groq_key() -> str:
    value = get_credential(CredentialProvider.GROQ, "api_key")
    if not value:
        raise RuntimeError("No Groq API key configured (admin dashboard or GROQ_API_KEY env var).")
    return value


def get_unsplash_key() -> str | None:
    """Unlike Groq, Unsplash is optional — the image pipeline falls back to
    AI generation when this isn't configured, so no exception here."""
    return get_credential(CredentialProvider.UNSPLASH, "access_key")


def get_gemini_key() -> str | None:
    """Optional same-day fallback used only when Groq's free-tier daily
    token cap is hit — no exception here, callers fall back to leaving the
    article for retry on the next cycle when this isn't configured."""
    return get_credential(CredentialProvider.GEMINI, "api_key")
