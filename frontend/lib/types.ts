export interface Category {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  sort_order: number;
  is_active: boolean;
}

export interface Article {
  id: string;
  source_id: string | null;
  category_id: string | null;
  title: string;
  summary: string | null;
  url: string;
  author: string | null;
  published_at: string | null;
  categories?: Pick<Category, "name" | "slug"> | null;
}

export interface GeneratedPost {
  id: string;
  article_id: string;
  headline: string | null;
  caption: string | null;
  summary: string | null;
  cta: string | null;
  hashtags: string[];
  image_prompt: string | null;
  image_url: string | null;
  quality_score: number | null;
  profanity_flag: boolean;
  approval_required: boolean;
  status: "draft" | "pending_review" | "approved" | "rejected" | "published" | "failed";
  created_at: string;
  articles?: Article;
}

export interface Source {
  id: string;
  name: string;
  type: "rss" | "api";
  url: string;
  category_id: string | null;
  is_active: boolean;
  fetch_interval_minutes: number | null;
  manual_approval: boolean;
  last_fetched_at: string | null;
  last_error: string | null;
}

export interface AIPrompt {
  id: string;
  name: string;
  category_id: string | null;
  prompt_type: string;
  template: string;
  is_active: boolean;
}

export interface JobRun {
  id: string;
  started_at: string;
  finished_at: string | null;
  status: "running" | "success" | "partial_failure" | "failed";
  articles_fetched: number;
  posts_generated: number;
  posts_published: number;
  errors_count: number;
}
