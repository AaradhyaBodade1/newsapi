# Supabase schema

This directory holds the Postgres schema (`migrations/`) and starter data (`seed.sql`) for the
News Platform. Everything runs on Supabase's free tier.

## One-time setup

1. Create a project at https://supabase.com (free tier).
2. Install the Supabase CLI: `npm install -g supabase` (or see https://supabase.com/docs/guides/cli).
3. From the **`backend/`** directory (the CLI expects `supabase/` as a direct child of the
   working directory), log in and link the project:
   ```bash
   cd backend
   supabase login
   supabase link --project-ref <your-project-ref>
   ```
4. Apply the schema:
   ```bash
   supabase db push
   ```
5. Load starter data (categories, example RSS sources, default settings, default AI prompt) —
   either `supabase db push --include-seed`, or:
   ```bash
   psql "$SUPABASE_DB_URL" -f supabase/seed.sql
   ```
   (or paste `seed.sql` into the Supabase SQL Editor).
6. Create your first admin user: sign up once via Supabase Auth (e.g. through the admin
   dashboard's `/admin/login` page using "sign up"), then insert a row so that user can manage
   the dashboard:
   ```sql
   insert into admin_users (id, email, role)
   values ('<the auth.users.id you just created>', 'you@example.com', 'admin');
   ```
7. Create a public Storage bucket named `post-images` (Storage → New bucket → Public) — this is
   where the worker uploads AI-generated images so they get a public URL for the website to
   consume.

## Files

- `migrations/0001_init.sql` — all tables, indexes, and `updated_at` triggers.
- `migrations/0002_rls.sql` — Row Level Security: public/anon gets read-only access to
  `categories` (active) and `generated_posts`/`articles` behind `status = 'published'`; everything
  else requires being listed in `admin_users`. The backend uses the **service role key**, which
  bypasses RLS entirely — never expose the service role key to the frontend.
- `migrations/0003_public_read_sources.sql` — adds the same public read-only policy to `sources`
  (active rows only). Without it the anon key silently gets `null` on any `sources` join instead
  of an error, which is easy to miss in development.
- `seed.sql` — starter categories, a handful of example RSS sources per category (verify/replace
  these — RSS URLs drift over time), default runtime `settings`, and one default AI prompt
  template used until you add per-category overrides from the admin dashboard.

## Notes on `credentials` and `settings`

- `credentials` stores encrypted values (Groq key, SMTP/webhook config) so they're
  editable from the admin dashboard instead of only via `.env`. The backend encrypts on write and
  decrypts on read using `CREDENTIALS_ENCRYPTION_KEY` (see `backend/.env.example`) — rotate that
  key and you'll need to re-enter credentials.
- `settings` is a simple key/value table read by the admin API (to render admin forms) and by the
  worker (to pick up posting frequency, retry limits, approval defaults, etc.) at the start of
  every cycle, so changes take effect on the next run without a redeploy.
