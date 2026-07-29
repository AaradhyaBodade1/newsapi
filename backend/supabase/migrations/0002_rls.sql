-- Row Level Security: public gets read-only access to published content,
-- admins (rows in admin_users) get full access, the backend/worker use the
-- Supabase service role key which bypasses RLS entirely.

alter table categories enable row level security;
alter table sources enable row level security;
alter table articles enable row level security;
alter table ai_prompts enable row level security;
alter table generated_posts enable row level security;
alter table publish_jobs enable row level security;
alter table settings enable row level security;
alter table credentials enable row level security;
alter table admin_users enable row level security;
alter table job_runs enable row level security;
alter table notification_logs enable row level security;

-- security definer helper so policies don't recurse into admin_users' own RLS
create or replace function is_admin() returns boolean as $$
  select exists (select 1 from admin_users where id = auth.uid());
$$ language sql stable security definer set search_path = public;

-- ---------------------------------------------------------------------------
-- public (anon) read-only access
-- ---------------------------------------------------------------------------
drop policy if exists "public read active categories" on categories;
create policy "public read active categories" on categories
  for select using (is_active = true);

drop policy if exists "public read published posts" on generated_posts;
create policy "public read published posts" on generated_posts
  for select using (status = 'published');

drop policy if exists "public read articles behind published posts" on articles;
create policy "public read articles behind published posts" on articles
  for select using (
    exists (
      select 1 from generated_posts gp
      where gp.article_id = articles.id and gp.status = 'published'
    )
  );

-- ---------------------------------------------------------------------------
-- admin (authenticated, present in admin_users) full access
-- ---------------------------------------------------------------------------
drop policy if exists "admin manage categories" on categories;
create policy "admin manage categories" on categories for all using (is_admin()) with check (is_admin());

drop policy if exists "admin manage sources" on sources;
create policy "admin manage sources" on sources for all using (is_admin()) with check (is_admin());

drop policy if exists "admin manage articles" on articles;
create policy "admin manage articles" on articles for all using (is_admin()) with check (is_admin());

drop policy if exists "admin manage ai_prompts" on ai_prompts;
create policy "admin manage ai_prompts" on ai_prompts for all using (is_admin()) with check (is_admin());

drop policy if exists "admin manage generated_posts" on generated_posts;
create policy "admin manage generated_posts" on generated_posts for all using (is_admin()) with check (is_admin());

drop policy if exists "admin manage publish_jobs" on publish_jobs;
create policy "admin manage publish_jobs" on publish_jobs for all using (is_admin()) with check (is_admin());

drop policy if exists "admin manage settings" on settings;
create policy "admin manage settings" on settings for all using (is_admin()) with check (is_admin());

drop policy if exists "admin manage credentials" on credentials;
create policy "admin manage credentials" on credentials for all using (is_admin()) with check (is_admin());

drop policy if exists "admin manage job_runs" on job_runs;
create policy "admin manage job_runs" on job_runs for all using (is_admin()) with check (is_admin());

drop policy if exists "admin manage notification_logs" on notification_logs;
create policy "admin manage notification_logs" on notification_logs for all using (is_admin()) with check (is_admin());

drop policy if exists "admin read own record" on admin_users;
create policy "admin read own record" on admin_users for select using (id = auth.uid());

drop policy if exists "admin manage admin_users" on admin_users;
create policy "admin manage admin_users" on admin_users for all using (is_admin()) with check (is_admin());
