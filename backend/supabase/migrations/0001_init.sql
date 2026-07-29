-- AI News Platform: initial schema
create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- categories
-- ---------------------------------------------------------------------------
create table if not exists categories (
  id uuid primary key default gen_random_uuid(),
  slug text unique not null,
  name text not null,
  description text,
  sort_order integer not null default 0,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- sources (RSS feeds / public APIs)
-- ---------------------------------------------------------------------------
create table if not exists sources (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  type text not null check (type in ('rss', 'api')),
  url text not null,
  category_id uuid references categories(id) on delete set null,
  is_active boolean not null default true,
  fetch_interval_minutes integer,
  manual_approval boolean not null default false,
  last_fetched_at timestamptz,
  last_error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- articles (raw ingested items, deduped by content_hash)
-- ---------------------------------------------------------------------------
create table if not exists articles (
  id uuid primary key default gen_random_uuid(),
  source_id uuid references sources(id) on delete set null,
  category_id uuid references categories(id) on delete set null,
  title text not null,
  summary text,
  raw_excerpt text,
  url text not null,
  author text,
  published_at timestamptz,
  fetched_at timestamptz not null default now(),
  content_hash text not null unique,
  status text not null default 'new' check (status in ('new', 'processing', 'processed', 'skipped', 'failed')),
  created_at timestamptz not null default now()
);
create index if not exists idx_articles_category on articles(category_id);
create index if not exists idx_articles_source on articles(source_id);
create index if not exists idx_articles_published_at on articles(published_at desc);
create index if not exists idx_articles_status on articles(status);

-- ---------------------------------------------------------------------------
-- ai_prompts (configurable prompt templates, optionally per category)
-- ---------------------------------------------------------------------------
create table if not exists ai_prompts (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  category_id uuid references categories(id) on delete cascade,
  prompt_type text not null check (
    prompt_type in ('master', 'headline', 'caption', 'summary', 'cta', 'hashtags', 'image_prompt')
  ),
  template text not null,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists idx_ai_prompts_category on ai_prompts(category_id);

-- ---------------------------------------------------------------------------
-- generated_posts (AI output per article)
-- ---------------------------------------------------------------------------
create table if not exists generated_posts (
  id uuid primary key default gen_random_uuid(),
  article_id uuid not null references articles(id) on delete cascade,
  headline text,
  caption text,
  summary text,
  cta text,
  hashtags text[] not null default '{}',
  image_prompt text,
  image_url text,
  quality_score numeric,
  profanity_flag boolean not null default false,
  approval_required boolean not null default false,
  status text not null default 'draft' check (
    status in ('draft', 'pending_review', 'approved', 'rejected', 'published', 'failed')
  ),
  reviewed_by uuid,
  reviewed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists idx_generated_posts_article on generated_posts(article_id);
create index if not exists idx_generated_posts_status on generated_posts(status);

-- ---------------------------------------------------------------------------
-- publish_jobs (per-platform publish attempts + retries)
-- ---------------------------------------------------------------------------
create table if not exists publish_jobs (
  id uuid primary key default gen_random_uuid(),
  generated_post_id uuid not null references generated_posts(id) on delete cascade,
  platform text not null check (platform in ('website')),
  external_post_id text,
  status text not null default 'pending' check (status in ('pending', 'success', 'failed', 'retrying')),
  attempt_count integer not null default 0,
  last_error text,
  published_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists idx_publish_jobs_post on publish_jobs(generated_post_id);
create index if not exists idx_publish_jobs_status on publish_jobs(status);

-- ---------------------------------------------------------------------------
-- settings (single source of truth for runtime configuration)
-- ---------------------------------------------------------------------------
create table if not exists settings (
  key text primary key,
  value jsonb not null,
  description text,
  updated_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- credentials (encrypted API keys/tokens, editable from the admin dashboard)
-- ---------------------------------------------------------------------------
create table if not exists credentials (
  id uuid primary key default gen_random_uuid(),
  provider text not null check (provider in ('groq', 'smtp', 'webhook')),
  key_name text not null,
  encrypted_value text not null,
  updated_at timestamptz not null default now(),
  unique (provider, key_name)
);

-- ---------------------------------------------------------------------------
-- admin_users (maps Supabase Auth users to dashboard roles)
-- ---------------------------------------------------------------------------
create table if not exists admin_users (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  role text not null default 'admin' check (role in ('admin', 'editor', 'viewer')),
  created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- job_runs (one row per worker cycle, for observability)
-- ---------------------------------------------------------------------------
create table if not exists job_runs (
  id uuid primary key default gen_random_uuid(),
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  status text not null default 'running' check (status in ('running', 'success', 'partial_failure', 'failed')),
  articles_fetched integer not null default 0,
  posts_generated integer not null default 0,
  posts_published integer not null default 0,
  errors_count integer not null default 0,
  summary jsonb
);
create index if not exists idx_job_runs_started_at on job_runs(started_at desc);

-- ---------------------------------------------------------------------------
-- notification_logs (failed-job alerts sent to admins)
-- ---------------------------------------------------------------------------
create table if not exists notification_logs (
  id uuid primary key default gen_random_uuid(),
  job_run_id uuid references job_runs(id) on delete set null,
  channel text not null check (channel in ('email', 'webhook')),
  message text not null,
  sent_at timestamptz not null default now(),
  success boolean not null default true
);

-- ---------------------------------------------------------------------------
-- updated_at triggers
-- ---------------------------------------------------------------------------
create or replace function set_updated_at() returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_sources_updated_at on sources;
create trigger trg_sources_updated_at before update on sources
  for each row execute function set_updated_at();

drop trigger if exists trg_ai_prompts_updated_at on ai_prompts;
create trigger trg_ai_prompts_updated_at before update on ai_prompts
  for each row execute function set_updated_at();

drop trigger if exists trg_generated_posts_updated_at on generated_posts;
create trigger trg_generated_posts_updated_at before update on generated_posts
  for each row execute function set_updated_at();

drop trigger if exists trg_publish_jobs_updated_at on publish_jobs;
create trigger trg_publish_jobs_updated_at before update on publish_jobs
  for each row execute function set_updated_at();
