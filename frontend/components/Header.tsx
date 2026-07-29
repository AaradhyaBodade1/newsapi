import Link from "next/link";
import { supabase } from "@/lib/supabaseClient";
import type { Category } from "@/lib/types";
import Logo from "@/components/Logo";

export const revalidate = 60;

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

export default async function Header() {
  const categories = await getCategories();

  return (
    <header className="sticky top-0 z-10 border-b border-neutral-200 dark:border-neutral-800 bg-white/90 dark:bg-neutral-950/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-3">
        <Link href="/" className="flex w-fit shrink-0 items-center gap-2.5 font-serif text-3xl font-bold tracking-tight text-brand-600 dark:text-brand-500">
          <Logo size={32} />
          Arka <span className="text-neutral-900 dark:text-white">News</span>
        </Link>
        <nav className="flex gap-5 overflow-x-auto pb-1 text-sm font-semibold">
          <Link
            href="/"
            className="whitespace-nowrap text-neutral-600 hover:text-brand-600 dark:text-neutral-300 dark:hover:text-brand-500 transition-colors"
          >
            All News
          </Link>
          {categories.map((category) => (
            <Link
              key={category.id}
              href={`/category/${category.slug}`}
              className="whitespace-nowrap text-neutral-600 hover:text-brand-600 dark:text-neutral-300 dark:hover:text-brand-500 transition-colors"
            >
              {category.name}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
