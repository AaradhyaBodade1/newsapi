-- Starter data: categories, example RSS sources, default settings, a master prompt.
-- Arka News covers India — source URLs below are Indian outlets (Times of India, The Hindu,
-- Economic Times, Moneycontrol, ESPN Cricinfo, Livemint, Bollywood Hungama), provided as a
-- starting point. Verify each still resolves and swap freely from the admin dashboard.

insert into categories (slug, name, description, sort_order) values
  ('technology',    'Technology',    'Tech industry, gadgets, software, AI', 1),
  ('business',      'Business',      'Companies, economy, markets, finance', 2),
  ('stock-market',  'Stock Market',  'Equities, indices, trading, earnings', 3),
  ('sports',        'Sports',        'Sports news and results', 4),
  ('entertainment', 'Entertainment', 'Movies, TV, music, celebrities', 5),
  ('health',        'Health',        'Health, medicine, wellness', 6),
  ('science',       'Science',       'Scientific research and discovery', 7),
  ('world',         'World News',    'International news and politics', 8),
  ('government',    'Government',    'Policy, government, public affairs', 9),
  ('education',     'Education',     'Schools, universities, education policy', 10)
on conflict (slug) do nothing;

insert into sources (name, type, url, category_id, is_active) values
  ('Times of India Tech',       'rss', 'https://timesofindia.indiatimes.com/rssfeeds/66949542.cms',              (select id from categories where slug = 'technology'),    true),
  ('Livemint Technology',       'rss', 'https://www.livemint.com/rss/technology',                                (select id from categories where slug = 'technology'),    true),
  ('Economic Times',            'rss', 'https://economictimes.indiatimes.com/rssfeedsdefault.cms',                (select id from categories where slug = 'business'),      true),
  ('Livemint Money',            'rss', 'https://www.livemint.com/rss/money',                                     (select id from categories where slug = 'business'),      true),
  ('The Hindu Business Line Markets', 'rss', 'https://www.thehindubusinessline.com/markets/feeder/default.rss',   (select id from categories where slug = 'stock-market'),  true),
  ('Economic Times Markets',    'rss', 'https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms',    (select id from categories where slug = 'stock-market'),  true),
  ('ESPN Cricinfo',             'rss', 'https://www.espncricinfo.com/rss/content/story/feeds/0.xml',              (select id from categories where slug = 'sports'),        true),
  ('Times of India Sports',     'rss', 'https://timesofindia.indiatimes.com/rssfeeds/4719148.cms',                (select id from categories where slug = 'sports'),        true),
  ('Times of India Entertainment', 'rss', 'https://timesofindia.indiatimes.com/rssfeeds/1081479906.cms',          (select id from categories where slug = 'entertainment'), true),
  ('Bollywood Hungama',         'rss', 'https://www.bollywoodhungama.com/rss/news.xml',                           (select id from categories where slug = 'entertainment'), true),
  ('Times of India Health',     'rss', 'https://timesofindia.indiatimes.com/rssfeeds/3908999.cms',                (select id from categories where slug = 'health'),        true),
  ('Times of India Science',    'rss', 'https://timesofindia.indiatimes.com/rssfeeds/-2128672765.cms',            (select id from categories where slug = 'science'),       true),
  ('Times of India World',      'rss', 'https://timesofindia.indiatimes.com/rssfeeds/296589292.cms',              (select id from categories where slug = 'world'),         true),
  ('The Hindu International',   'rss', 'https://www.thehindu.com/news/international/feeder/default.rss',          (select id from categories where slug = 'world'),         true),
  ('The Hindu National',        'rss', 'https://www.thehindu.com/news/national/feeder/default.rss',                (select id from categories where slug = 'government'),    true),
  ('Times of India India News', 'rss', 'https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms',            (select id from categories where slug = 'government'),    true),
  ('Times of India Education',  'rss', 'https://timesofindia.indiatimes.com/rssfeeds/913168846.cms',              (select id from categories where slug = 'education'),     true)
on conflict do nothing;

insert into settings (key, value, description) values
  ('posting_frequency_minutes', '20',    'How often a worker cycle should run. This is informational for the admin UI; the actual interval is set by LOOP_INTERVAL_MINUTES in backend/.env (in-process scheduler).'),
  ('manual_approval_default',   'false', 'Whether newly generated posts require manual admin approval before publishing, when a source/category does not override it.'),
  ('max_retry_attempts',        '3',     'Maximum retry attempts per publish_jobs row before it is marked failed and a notification is sent.'),
  ('max_articles_per_run',      '20',    'Safety cap on the number of new articles processed in a single worker cycle.'),
  ('quality_score_threshold',   '0.6',   'Minimum AI self-reported quality score (0-1) required to auto-approve a post.'),
  ('notification_email',        '""',    'Email address that receives failed-job notifications (set from the admin dashboard).'),
  ('notification_webhook_url',  '""',    'Optional webhook URL (e.g. Slack incoming webhook) that receives failed-job notifications.')
on conflict (key) do nothing;

insert into ai_prompts (name, category_id, prompt_type, template, is_active) values (
  'Default master prompt',
  null,
  'master',
  'You are a professional editor for Arka News, an Indian news website. You will be given a news article''s title, summary, source, category, and URL. '
  || 'Arka News only publishes stories that are about India, or that have a clear, explainable impact/relevance on India or Indians (e.g. global markets moving Indian stocks, foreign policy involving India, an international sports event India is competing in). '
  || 'If the article has no such connection to India, do not force one — honestly report it as not relevant instead of inventing a link. '
  || 'Write ENTIRELY ORIGINAL content in a clear, professional journalistic tone that accurately captures the key facts without copying any sentence from the source, and without fabricating facts not present in the input. '
  || 'Do not use emojis, slang, or clickbait phrasing anywhere in the output. '
  || 'Return strict JSON with these keys: headline (<=90 chars, clear and informative, not sensational), '
  || 'caption (a single crisp, tightly-written paragraph of about 10 lines / 120-160 words, not a bullet list, not separated by newlines, no filler sentences or padding, plain professional language, no emojis), '
  || 'summary (<=280 chars, neutral factual recap), '
  || 'cta (one short, non-emoji call-to-action sentence inviting readers to read more or share), hashtags (array of 5-8 relevant hashtags without the # symbol), '
  || 'image_prompt (a detailed, safe-for-work prompt describing a photorealistic photograph representing the story, natural lighting, DSLR quality, NOT an illustration or painting, no text/logos/real public figures'' faces), '
  || 'quality_score (0-1 float, your own confidence that this is factual, original, and publish-ready), '
  || 'is_india_relevant (boolean, true only if the story is about India or clearly affects India).',
  true
)
on conflict do nothing;
