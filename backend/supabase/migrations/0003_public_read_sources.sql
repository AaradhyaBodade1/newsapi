-- The article detail page shows which source a story came from
-- (frontend/app/article/[id]/page.tsx joins articles.sources(name)), but the
-- anon key had no read policy on `sources` — RLS silently returned null for
-- the join instead of erroring, so every article showed "an external
-- publisher" instead of the real source name. Sources are just RSS feed
-- metadata (name/url), nothing sensitive, so this mirrors the existing
-- "public read active categories" policy.

drop policy if exists "public read active sources" on sources;
create policy "public read active sources" on sources
  for select using (is_active = true);
