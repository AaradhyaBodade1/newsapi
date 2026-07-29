-- The worker now prefers the source's own article image (from RSS enclosure/
-- media tags or an <img> embedded in the summary HTML) over generating one
-- with AI, falling back to AI generation only when the source provides none.
-- This column carries that source image URL from ingestion through to the
-- generate step, which runs in a later pass over articles.status = 'new'.

alter table articles add column if not exists image_url text;
