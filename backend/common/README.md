# common — shared package (app + worker)

Small Python package with no service-specific logic, imported by both `backend/app/` (the FastAPI
admin API) and `backend/worker/` (the ingestion/generation/publishing pipeline) so a change (a new
enum value, a schema field, an encryption fix) only has to happen once and both stay in sync.

Not runnable on its own — no entrypoint. It lives alongside `app/` and `worker/` inside the single
`backend/` package, so `from common.xxx import ...`, `from app.xxx import ...`, and
`from worker.xxx import ...` all resolve when running from `backend/` with `PYTHONPATH=.`.

## Files

| File | Purpose |
|---|---|
| `enums.py` | Shared string enums mirroring the Postgres `check` constraints in `supabase/migrations/0001_init.sql` (`SourceType`, `ArticleStatus`, `PromptType`, `PostStatus`, `Platform`, `PublishStatus`, `CredentialProvider`, `JobRunStatus`) — keeps Python and DB status values from drifting apart. |
| `schemas.py` | Pydantic models for the core domain objects (`Category`, `Source`, `Article`, `AIPrompt`, `GeneratedContent`, `GeneratedPost`, `PublishJob`). `GeneratedContent` is the strict shape the worker requires back from the AI text-generation call. |
| `supabase_client.py` | `get_supabase()` — a cached Supabase client built from `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`. Service-role only: bypasses Row Level Security, so this must never be imported by the frontend. |
| `security.py` | `encrypt_value` / `decrypt_value` — Fernet symmetric encryption for the `credentials` table, keyed by `CREDENTIALS_ENCRYPTION_KEY` in `backend/.env`. |
| `credentials_store.py` | Typed reads/writes against the `credentials` table (`get_groq_key`, `get_credential`/`set_credential`). Falls back to plain env vars (`GROQ_API_KEY`, etc.) when nothing has been configured from the admin dashboard yet. |
| `settings_store.py` | Typed reads/writes against the `settings` key/value table, with `DEFAULTS` used whenever a key hasn't been set yet — read fresh every worker cycle so dashboard changes apply without a redeploy. |
| `logging_config.py` | `configure_logging(service_name)` — one JSON-per-line log formatter for both services, so Render/Railway/GitHub Actions log output is greppable. |
| `dedupe.py` | `compute_content_hash(title, url)` — the article de-duplication hash (normalizes the URL by stripping tracking params/fragments, normalizes whitespace/case on the title) used by the worker's ingestion step and enforced by the `articles.content_hash` unique constraint. |

## Adding something here

Only put code here if **both** `app` and `worker` need it. Anything used by just one belongs in
that package instead — pulling it into `common` prematurely just adds an import hop with no
payoff.

## Tests

`common` has no tests of its own — its behavior is exercised indirectly through `backend/tests`
and `backend/worker/tests` (e.g. `backend/worker/tests/test_dedupe.py` covers `dedupe.py`).
