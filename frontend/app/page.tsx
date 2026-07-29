import { supabase } from "@/lib/supabaseClient";
import type { Category, GeneratedPost } from "@/lib/types";
import ArticleCard from "@/components/ArticleCard";
import SectionHeading from "@/components/SectionHeading";

export const revalidate = 60;

const SELECT_WITH_CATEGORY = "*, articles(*, categories(name, slug))";

async function getCategories(): Promise<Category[]> {
  const { data, error } = await supabase
    .from("categories")
    .select("*")
    .eq("is_active", true)
    .order("sort_order");

  if (error) {
    console.error("Failed to load categories", error.message);
    return [];
  }
  return data ?? [];
}

async function getLatestPosts(limit: number): Promise<GeneratedPost[]> {
  const { data, error } = await supabase
    .from("generated_posts")
    .select(SELECT_WITH_CATEGORY)
    .eq("status", "published")
    .order("created_at", { ascending: false })
    .limit(limit);

  if (error) {
    console.error("Failed to load latest posts", error.message);
    return [];
  }
  return data ?? [];
}

async function getCategoryPosts(categoryId: string, limit: number): Promise<GeneratedPost[]> {
  const { data, error } = await supabase
    .from("generated_posts")
    .select("*, articles!inner(*, categories(name, slug))")
    .eq("status", "published")
    .eq("articles.category_id", categoryId)
    .order("created_at", { ascending: false })
    .limit(limit);

  if (error) {
    console.error("Failed to load category posts", error.message);
    return [];
  }
  return data ?? [];
}

export default async function HomePage() {
  const [latest, categories] = await Promise.all([getLatestPosts(9), getCategories()]);

  if (latest.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 py-24 text-center">
        <h1 className="text-xl font-semibold text-neutral-900 dark:text-white">No published articles yet</h1>
        <p className="max-w-md text-neutral-500">
          Once the worker generates and publishes its first stories, they will appear here
          automatically.
        </p>
      </div>
    );
  }

  const categoryPostLists = await Promise.all(categories.map((category) => getCategoryPosts(category.id, 4)));
  const sections = categories
    .map((category, i) => ({ category, posts: categoryPostLists[i] }))
    .filter((section) => section.posts.length > 0);

  return (
    <div className="flex flex-col gap-16">
      <section className="flex flex-col gap-6">
        <SectionHeading title="All News" />
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {latest.map((post) => (
            <ArticleCard key={post.id} post={post} />
          ))}
        </div>
      </section>

      {sections.map(({ category, posts }) => (
        <section key={category.id} className="flex flex-col gap-6">
          <SectionHeading title={category.name} href={`/category/${category.slug}`} />
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {posts.map((post) => (
              <ArticleCard key={post.id} post={post} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
