import Link from "next/link";

export default function SectionHeading({ title, href }: { title: string; href?: string }) {
  return (
    <div className="flex items-end justify-between gap-4 border-b border-neutral-200 dark:border-neutral-800 pb-3">
      <h2 className="flex items-center gap-3 font-serif text-2xl font-bold tracking-tight text-neutral-900 dark:text-white">
        <span className="h-6 w-1.5 shrink-0 rounded-full bg-brand-600 dark:bg-brand-500" aria-hidden />
        {title}
      </h2>
      {href ? (
        <Link
          href={href}
          className="shrink-0 text-sm font-medium text-brand-600 hover:text-brand-700 dark:text-brand-500 dark:hover:text-brand-400 transition-colors"
        >
          View all &rarr;
        </Link>
      ) : null}
    </div>
  );
}
