-- Allow storing a Gemini API key (used as a same-day fallback for text
-- generation when Groq's free-tier 100k-tokens/day cap is hit) via the
-- admin dashboard's Credentials page.

alter table credentials drop constraint if exists credentials_provider_check;
alter table credentials add constraint credentials_provider_check
  check (provider in ('groq', 'gemini', 'unsplash', 'smtp', 'webhook'));
