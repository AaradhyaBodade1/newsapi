import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { supabase } from "@/lib/supabaseClient";
import type { GeneratedPost } from "@/lib/types";

export const revalidate = 60;

async function getPost(id: string): Promise<GeneratedPost | null> {
  const { data } = await supabase
    .from("generated_posts")
    .select("*, articles(*, categories(name, slug))")
    .eq("id", id)
    .eq("status", "published")
    .limit(1);
  return data?.[0] ?? null;
}

export default async function ArticlePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const post = await getPost(id);
  if (!post) {
    notFound();
  }

  const publishedAt = post.articles?.published_at ?? post.created_at;
  const category = post.articles?.categories;

  return (
    <article className="mx-auto flex max-w-2xl flex-col gap-7">
      <div className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center gap-3 text-xs font-semibold uppercase tracking-wide text-neutral-400">
          {category ? (
            <Link
              href={`/category/${category.slug}`}
              className="rounded-full bg-brand-600 px-2.5 py-1 text-white hover:bg-brand-700 transition-colors"
            >
              {category.name}
            </Link>
          ) : null}
          <time dateTime={publishedAt}>
            {new Date(publishedAt).toLocaleDateString("en-US", {
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </time>
        </div>
        <h1 className="font-serif text-4xl font-bold leading-[1.15] tracking-tight text-neutral-900 dark:text-white sm:text-5xl">
          {post.headline}
        </h1>
        <p className="font-serif text-xl leading-snug text-neutral-500 dark:text-neutral-400">{post.summary}</p>
      </div>

      {post.image_url ? (
        <div className="relative aspect-video overflow-hidden rounded-xl bg-neutral-100 dark:bg-neutral-900">
          <Image src={post.image_url} alt={post.headline ?? ""} fill className="object-cover" priority />
        </div>
      ) : null}

      <div className="flex flex-col gap-4 font-serif text-[1.2rem] leading-[1.7] text-neutral-800 dark:text-neutral-200">
        <p className="whitespace-pre-line">{post.caption}</p>
        {post.cta ? <p className="font-semibold">{post.cta}</p> : null}
      </div>

      {post.hashtags?.length ? (
        <div className="flex flex-wrap gap-2 text-sm text-brand-600 dark:text-brand-500">
          {post.hashtags.map((tag) => (
            <span key={tag}>#{tag}</span>
          ))}
        </div>
      ) : null}
    </article>
  );
}
