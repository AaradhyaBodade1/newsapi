-- Allow storing an Unsplash Access Key (used as the middle tier of the image
-- fallback chain: source's own image -> Unsplash keyword search -> AI
-- generation) via the admin dashboard's Credentials page.

alter table credentials drop constraint if exists credentials_provider_check;
alter table credentials add constraint credentials_provider_check
  check (provider in ('groq', 'unsplash', 'smtp', 'webhook'));
