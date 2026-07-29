# Backend — Admin API + Worker (FastAPI)

Single service, two responsibilities:

- **Admin API** (`app/`) — REST API used by the `/admin` section of the frontend to manage
  sources, categories, AI prompts, settings, credentials, the manual-approval review queue, and
  dashboard stats/logs.
- **Worker** (`worker/`) — on an in-process scheduler (APScheduler), runs an ingest → generate →
  publish cycle every `LOOP_INTERVAL_MINUTES` (default 20): pulls new articles from configured
  Indian RSS/API sources, dedupes them, calls Groq (free tier) for an original crisp caption and
  Pollinations.ai (free, no key) for a photorealistic image, runs them through a quality gate
  (including a self-reported India-relevance check), and publishes to the website.

The public website does **not** call this API — it reads published content directly from
Supabase with the anon key (RLS-protected, read-only). This service always uses the Supabase
**service role key** and is never exposed to the public site.

`common/` holds code shared by both halves (enums, Pydantic schemas, the Supabase client,
credential encryption, settings access, logging) — see `common/README.md`.

## Auth model

Admins sign in via Supabase Auth (email/password) from the frontend. The frontend sends the
resulting JWT as `Authorization: Bearer <token>`. This API verifies the JWT against Supabase's
public JWKS (`{SUPABASE_URL}/auth/v1/.well-known/jwks.json`) and then checks the user exists in
the `admin_users` table (see `supabase/README.md` for how to create your first admin).

## Local development

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in Supabase URL/keys, encryption key, Groq key
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

Visit http://localhost:8000/health and http://localhost:8000/docs (OpenAPI UI). The worker
scheduler starts automatically with the server (see startup logs) and runs its first cycle
immediately, then every `LOOP_INTERVAL_MINUTES`.

To force a single worker cycle without running the full server (useful for quick iteration):

```bash
PYTHONPATH=. python -m worker.main
```

## Tests

```bash
PYTHONPATH=. pytest
```

Discovers both `tests/` (admin API) and `worker/tests/` (ingestion dedupe, quality gate, generic
API fetcher — these don't hit Groq/Pollinations/Supabase over the network).

## Docker

```bash
docker build -t arka-news-backend backend
docker run --env-file backend/.env -p 8000:8000 arka-news-backend
```

## Deployment

Deploy as a single always-on web service on a free tier (Render/Railway/Fly.io — any Docker
host):

1. Connect the repo, point the build at `backend/Dockerfile` with build context `backend/`.
2. Copy every var from `.env.example` into the platform's environment settings with real values
   (Supabase keys, a generated `CREDENTIALS_ENCRYPTION_KEY`, Groq key, `CORS_ORIGINS` including
   your deployed frontend's real domain).
3. Set `ENVIRONMENT=production`.
4. Make sure the platform's port setting matches the container's exposed `8000` (the Dockerfile's
   `CMD` binds `uvicorn` to `0.0.0.0:8000`; most Docker-based hosts detect this from `EXPOSE`
   automatically — check the platform's docs if the service fails to receive traffic).
5. Point the frontend's `NEXT_PUBLIC_BACKEND_API_URL` at this service's public URL.

No separate cron job or worker service is needed — the worker cycle runs on the in-process
scheduler as long as this service is up.

## Credentials

The Groq credential (and SMTP/webhook for failure notifications) is read first from the
`credentials` table (encrypted, editable from the admin dashboard), falling back to this
service's `.env` if nothing is configured there yet — see `common/credentials_store.py`. Image
generation (Pollinations.ai) needs no credential at all.

## Key routes

| Route | Purpose |
|---|---|
| `GET /health` | Liveness check |
| `GET/POST/PATCH/DELETE /api/v1/categories` | Manage categories shown in the website header |
| `GET/POST/PATCH/DELETE /api/v1/sources` | Manage RSS/API news sources |
| `GET /api/v1/articles` | Browse ingested articles |
| `GET/POST/PATCH/DELETE /api/v1/prompts` | Manage AI prompt templates (global or per-category) |
| `GET/PATCH /api/v1/posts`, `POST /api/v1/posts/{id}/approve|reject` | Manual-approval review queue |
| `GET/PUT /api/v1/settings` | Posting frequency, retry limits, approval default, quality threshold |
| `GET/PUT/DELETE /api/v1/credentials` | Store encrypted Groq/SMTP credentials (values never read back) |
| `GET /api/v1/dashboard/stats\|job-runs\|notifications` | Dashboard overview + logs |

## Worker pipeline, step by step

1. **Ingest** — fetch every active source (RSS via `feedparser`, or generic JSON APIs), normalize
   fields, compute a dedupe hash (title+URL, tracking params stripped), insert genuinely new rows
   into `articles`.
2. **Generate** — for up to `max_articles_per_run` new articles, call Groq's free-tier API (JSON
   mode) with a configurable prompt (per-category override or the global default from
   `ai_prompts`) to produce an original headline, caption, summary, CTA, hashtags, and an image
   prompt — never copying the source's wording.
3. **Quality gate** — profanity filter + length/shape checks + the AI's own self-reported
   `quality_score` against `settings.quality_score_threshold`. Failing content is stored with
   `status=rejected` instead of being published.
4. **Image** — Pollinations.ai (free, no API key) generates an image from the AI's own image
   prompt, uploaded to the Supabase Storage `post-images` bucket for a public URL.
5. **Approval branch** — if manual approval is enabled (globally via `settings` or per-source via
   `sources.manual_approval`), the post stops at `status=pending_review` for the admin dashboard.
   Otherwise it's `approved` immediately (the default, per current configuration).
6. **Publish** — every `approved` post (new this cycle, or approved from the review queue since
   the last cycle) gets "published" to the website by flipping its status (the public site reads
   `generated_posts` directly from Supabase). The attempt is retried with exponential backoff and
   recorded in `publish_jobs`.
7. **Notify** — if any errors occurred this cycle, a summary is emailed/webhooked (whichever is
   configured under `settings.notification_email` / `notification_webhook_url`) and logged to
   `notification_logs`.
8. A `job_runs` row records fetch/generate/publish counts and errors for the admin "Logs" page.
