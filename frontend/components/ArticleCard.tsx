import Image from "next/image";
import Link from "next/link";
import type { GeneratedPost } from "@/lib/types";

export default function ArticleCard({ post }: { post: GeneratedPost }) {
  const publishedAt = post.articles?.published_at ?? post.created_at;
  const category = post.articles?.categories;

  return (
    <Link
      href={`/article/${post.id}`}
      className="group flex flex-col overflow-hidden rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900/40 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200"
    >
      <div className="relative aspect-video bg-neutral-100 dark:bg-neutral-900 overflow-hidden">
        {post.image_url ? (
          <Image
            src={post.image_url}
            alt={post.headline ?? "Article image"}
            fill
            sizes="(max-width: 768px) 100vw, 33vw"
            className="object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : null}
        {category ? (
          <span className="absolute left-3 top-3 rounded-full bg-brand-600 px-2.5 py-1 text-xs font-semibold uppercase tracking-wide text-white shadow-sm">
            {category.name}
          </span>
        ) : null}
      </div>
      <div className="flex flex-col gap-2 p-4">
        <time className="text-xs font-medium uppercase tracking-wide text-neutral-400" dateTime={publishedAt}>
          {new Date(publishedAt).toLocaleDateString("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric",
          })}
        </time>
        <h3 className="font-serif text-lg font-semibold leading-snug text-neutral-900 dark:text-white group-hover:text-brand-600 dark:group-hover:text-brand-500 transition-colors">
          {post.headline}
        </h3>
        <p className="text-sm text-neutral-600 dark:text-neutral-400 line-clamp-3">{post.summary}</p>
      </div>
    </Link>
  );
}
