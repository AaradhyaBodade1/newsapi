# Frontend — public website + admin dashboard (Next.js)

One Next.js app, two audiences:

- **Public site** (`/`, `/category/[slug]`, `/article/[id]`) — server components reading directly
  from Supabase with the anon key. Row Level Security restricts this to `is_active` categories and
  `status='published'` posts/articles, so this is safe even though it's a public/browser key.
  The header navigation is generated from the `categories` table, so adding a category (e.g. a new
  "Stock Market" or "Government" section) from the admin dashboard adds a nav link automatically.
  Styled as an editorial reading experience: `Source Serif 4` (via `next/font/google`) for
  headlines and article body copy, `Inter` for UI chrome — see `app/layout.tsx` and
  `tailwind.config.ts`'s `fontFamily` extension.
- **Admin dashboard** (`/admin/*`) — client components. Sign-in uses Supabase Auth; the resulting
  JWT is sent as a Bearer token to the FastAPI backend for anything that mutates config
  (sources, categories, prompts, settings, credentials) or the review queue. See
  `../backend/supabase/README.md` for how to promote a signed-up user to an admin.

## Local development

```bash
cd frontend
npm install
cp .env.example .env.local   # fill in Supabase URL/anon key + backend API URL
npm run dev
```

Visit http://localhost:3000 for the public site and http://localhost:3000/admin for the
dashboard (requires the backend running locally too, and an admin_users row for your account).

## Build

```bash
npm run build   # production build — runs ESLint + type-check as a hard gate (next dev does not)
npm run start   # serve that build locally on :3000, for a final smoke test before deploying
```

## Deployment (Netlify)

1. Push this repo to GitHub and connect it in Netlify, with **Base directory** set to `frontend`.
2. Netlify auto-detects `netlify.toml` (uses `@netlify/plugin-nextjs`) and runs `npm run build`
   itself on every push — no manual deploy command needed.
3. Set the environment variables from `.env.example` in Netlify's Site settings → Environment
   variables (use the production Supabase project + the deployed backend URL).
4. Deploy. Netlify's free tier covers this comfortably for a low/moderate-traffic site.

Before pushing, run `npm run build` locally at least once — it catches lint/type errors that
`npm run dev` silently allows, and a failing build here means a failing Netlify deploy.

## Structure

- `app/(public)` pages read Supabase directly — no admin auth needed.
- `app/admin/login` is intentionally outside the `(protected)` route group so unauthenticated
  users can reach it; `app/admin/(protected)/layout.tsx` guards everything else and redirects to
  `/admin/login` if there's no session or the user isn't in `admin_users`.
- `lib/supabaseClient.ts` — anon-key Supabase client (public reads).
- `lib/api.ts` — fetch wrapper that attaches the admin's Supabase JWT and calls the FastAPI
  backend.
