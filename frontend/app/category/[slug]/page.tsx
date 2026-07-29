import { notFound } from "next/navigation";
import { supabase } from "@/lib/supabaseClient";
import type { Category, GeneratedPost } from "@/lib/types";
import ArticleCard from "@/components/ArticleCard";

export const revalidate = 60;

async function getCategory(slug: string): Promise<Category | null> {
  const { data } = await supabase.from("categories").select("*").eq("slug", slug).eq("is_active", true).limit(1);
  return data?.[0] ?? null;
}

async function getPostsForCategory(categoryId: string): Promise<GeneratedPost[]> {
  const { data, error } = await supabase
    .from("generated_posts")
    .select("*, articles!inner(*, categories(name, slug))")
    .eq("status", "published")
    .eq("articles.category_id", categoryId)
    .order("created_at", { ascending: false })
    .limit(48);

  if (error) {
    console.error("Failed to load category posts", error.message);
    return [];
  }
  return data ?? [];
}

export default async function CategoryPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const category = await getCategory(slug);
  if (!category) {
    notFound();
  }

  const posts = await getPostsForCategory(category.id);

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-2 border-b border-neutral-200 dark:border-neutral-800 pb-6">
        <h1 className="flex items-center gap-3 font-serif text-4xl font-bold tracking-tight text-neutral-900 dark:text-white">
          <span className="h-7 w-1.5 shrink-0 rounded-full bg-brand-600 dark:bg-brand-500" aria-hidden />
          {category.name}
        </h1>
        {category.description ? <p className="text-neutral-500 dark:text-neutral-400">{category.description}</p> : null}
      </div>
      {posts.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-16 text-center">
          <p className="font-medium text-neutral-700 dark:text-neutral-300">No published articles in this category yet</p>
          <p className="max-w-md text-sm text-neutral-500">Check back soon — new stories are published automatically.</p>
        </div>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {posts.map((post) => (
            <ArticleCard key={post.id} post={post} />
          ))}
        </div>
      )}
    </div>
  );
}
