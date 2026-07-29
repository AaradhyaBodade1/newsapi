# Arka News — AI News Aggregation & Auto-Publishing Platform

An India-focused news site: on a configurable interval (`LOOP_INTERVAL_MINUTES`, default 20 — a
full cycle takes 10-15+ min on the free-tier services this runs on) it pulls new articles from
configured Indian RSS/API sources, dedupes them, uses Groq (free tier) to write an original crisp
caption (and self-checks whether the story is actually about India or affects India before
publishing) and Pollinations.ai (free, no key) to generate a photorealistic image for each (never
copying the source), then auto-publishes to a public website with category sections in the header
— with logging, retries, and failure notifications throughout. An admin dashboard configures
sources, categories, AI prompts, posting schedule, credentials, and (optionally) a manual-approval
review queue before anything goes live.

The public site is styled as an editorial reading experience (serif headlines/body via
`Source Serif 4`, sans-serif UI via `Inter`) rather than a typical dashboard-style feed.

Two deployable folders, nothing else:

```
                         ┌──────────────────────────────────────────┐
   RSS / public APIs ───▶│  backend/  (FastAPI, single service)      │
                         │  ├─ app/     admin REST API                │
                         │  ├─ worker/  in-process scheduler: every    │
                         │  │           N min, generates text (Groq)   │
                         │  │           + image (Pollinations), then   │
                         │  │           publishes                      │
                         │  ├─ common/  shared code (both above)       │
                         │  └─ supabase/  schema migrations + seed      │
                         └─────────────────────┬──────────────────────┘
                                                │ service role key
                                                ▼
                                     ┌────────────────────┐
                                     │      Supabase        │◀──────────────┐
                                     │  Postgres + Auth +    │                │ admin JWT
                                     │  Storage (free tier)  │                │ (Supabase Auth)
                                     └─────────┬────────────┘        ┌────────┴─────────┐
                                                │ anon key, RLS       │ frontend/ (Next.js) │
                                                │ read-only            │ public site + /admin│
                                                └──────────────────────▶ deployed on Netlify  │
                                                                       └──────────────────────┘
```

- **`backend/`** — one FastAPI service with two jobs: serve the admin REST API (sources,
  categories, prompts, settings, credentials, review queue, dashboard stats/logs) and, on an
  in-process scheduler, run the ingest → generate → publish worker cycle. Uses the Supabase
  **service role key**; never exposed to the public site. Also holds `common/` (shared code) and
  `supabase/` (schema migrations, RLS policies, seed data) — see `backend/README.md`.
- **`frontend/`** — one Next.js app: the public website (header nav built from the `categories`
  table — Technology, Business, Stock Market, Sports, Entertainment, Health, Science, World News,
  Government, Education) and the `/admin` dashboard. Deployed to **Netlify**.

## Quickstart

1. **Supabase**: create a free project, apply `backend/supabase/migrations`, load
   `backend/supabase/seed.sql`, create the `post-images` Storage bucket, and create your first
   admin user. Full steps in `backend/supabase/README.md`.
2. **Backend**: `cd backend && cp .env.example .env` (fill in Supabase keys, a generated
   `CREDENTIALS_ENCRYPTION_KEY`, and a free Groq API key from https://console.groq.com/keys — or
   configure Groq later from the admin dashboard; image generation needs no key), then
   `backend/README.md` to run locally or deploy. The worker cycle starts automatically with the
   server — no separate process or cron job to set up.
3. **Frontend**: `cd frontend && cp .env.example .env.local && npm install && npm run dev`, then
   `frontend/README.md` for deploying to Netlify.
4. In the admin dashboard (`/admin`), add sources per category, review/tune the default AI prompt,
   configure the Groq credential, and adjust settings (posting frequency, retry limits,
   manual-approval default). **Manual approval is off by default** (posts publish automatically)
   — turn it on globally in Settings or per-source in Sources if you want a review step first.

## Deployment summary (all free tiers)

| Component | Where | Why |
|---|---|---|
| Database/Auth/Storage | Supabase free tier | Postgres + RLS, Auth, Storage bucket for images |
| Backend (API + worker) | Render/Railway free web service | Single always-on service; the worker cycle runs on its in-process scheduler, no separate cron job needed |
| Frontend | Netlify free tier | `@netlify/plugin-nextjs`, base directory `frontend` |

## Deploy commands

**Before deploying anything**, apply pending Supabase migrations (see `backend/supabase/README.md`):
```bash
cd backend && supabase db push
```

**Backend** (Docker, any host — Render/Railway/Fly.io point their Dockerfile build at `backend/`):
```bash
docker build -t arka-news-backend backend
docker run --env-file backend/.env -p 8000:8000 arka-news-backend
```
On Render/Railway: connect the repo, set the Dockerfile path to `backend/Dockerfile` with build
context `backend/`, copy every var from `backend/.env.example` into the platform's environment
settings (real values), and make sure the service's port setting matches the container's exposed
`8000`. No separate worker/cron service — this one process does both.

**Frontend** — Netlify auto-builds on push once connected (base directory `frontend`, uses
`netlify.toml`), no manual command needed. To reproduce that build locally (e.g. to catch
lint/type errors — `next build` runs ESLint as a hard gate that `next dev` does not):
```bash
cd frontend
npm run build   # production build; fails on lint/type errors dev mode won't catch
npm run start   # serves the production build locally on :3000, for a final smoke test
```

## CI/CD

`.github/workflows/`: `backend.yml` runs tests (admin API + worker pipeline) on every PR and (on
push to `main`) builds the Docker image and optionally hits a deploy hook
(`BACKEND_DEPLOY_HOOK_URL` repo secret — set this once you've created the Render/Railway service).
`frontend.yml` lints/builds as a CI gate (actual deploy is Netlify's own GitHub integration).
`supabase-migrate.yml` applies new migrations on push if `SUPABASE_ACCESS_TOKEN` /
`SUPABASE_PROJECT_REF` secrets are set.

## Compliance note

The worker's prompts explicitly instruct the AI to write **original** captions/summaries from the
facts in an article, never to copy the source's wording — that's the only safeguard against
republishing copyrighted text. The public site does **not** display AI-generation disclosure or
link back to the original source (removed by product decision); the underlying data is still
there (`articles.url`, `articles.source_id`) if you want to reinstate either later. Without visible
attribution, you're relying entirely on the "originality" of each generated caption to stay clear
of copyright issues — review each source's terms of service (some feeds restrict commercial reuse
even of facts/summaries) and note that removing AI-content disclosure may also run against
disclosure norms/regulations in some jurisdictions for AI-generated news content.
