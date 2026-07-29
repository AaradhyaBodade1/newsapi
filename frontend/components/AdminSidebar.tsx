"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { supabase } from "@/lib/supabaseClient";

const LINKS = [
  { href: "/admin", label: "Dashboard" },
  { href: "/admin/review", label: "Review queue" },
  { href: "/admin/sources", label: "Sources" },
  { href: "/admin/categories", label: "Categories" },
  { href: "/admin/prompts", label: "AI prompts" },
  { href: "/admin/settings", label: "Settings" },
  { href: "/admin/credentials", label: "Credentials" },
  { href: "/admin/logs", label: "Logs" },
];

export default function AdminSidebar({ email }: { email: string }) {
  const pathname = usePathname();
  const router = useRouter();

  async function signOut() {
    await supabase.auth.signOut();
    router.push("/admin/login");
  }

  return (
    <aside className="flex flex-col gap-3 border-b border-slate-200 pb-4 dark:border-slate-800 lg:w-56 lg:shrink-0 lg:gap-1 lg:border-b-0 lg:border-r lg:py-6 lg:pb-0 lg:pr-4">
      <nav className="flex flex-row gap-1 overflow-x-auto lg:flex-col">
        {LINKS.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={`whitespace-nowrap rounded px-3 py-2 text-sm font-medium ${
              pathname === link.href
                ? "bg-brand-50 text-brand-700 dark:bg-brand-500/10 dark:text-brand-500"
                : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-900"
            }`}
          >
            {link.label}
          </Link>
        ))}
      </nav>
      <div className="flex flex-row items-center justify-between gap-2 text-xs text-slate-400 lg:mt-auto lg:flex-col lg:items-start lg:pt-6">
        <span className="truncate">{email}</span>
        <button onClick={signOut} className="shrink-0 underline underline-offset-2 hover:text-slate-600">
          Sign out
        </button>
      </div>
    </aside>
  );
}
