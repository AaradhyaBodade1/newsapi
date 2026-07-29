"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface Stats {
  articles_total: number;
  articles_new: number;
  posts_pending_review: number;
  posts_published: number;
  posts_failed: number;
  publish_jobs_failed: number;
  sources_active: number;
}

const LABELS: Record<keyof Stats, string> = {
  articles_total: "Articles ingested",
  articles_new: "Articles awaiting generation",
  posts_pending_review: "Posts pending review",
  posts_published: "Posts published",
  posts_failed: "Posts rejected/failed",
  publish_jobs_failed: "Failed publish attempts",
  sources_active: "Active sources",
};

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Stats>("/api/v1/dashboard/stats")
      .then(setStats)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load stats"));
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      {error ? <p className="text-red-600 text-sm">{error}</p> : null}
      {!stats && !error ? <p className="text-slate-500">Loading…</p> : null}
      {stats ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {(Object.keys(LABELS) as (keyof Stats)[]).map((key) => (
            <div key={key} className="rounded-lg border border-slate-200 dark:border-slate-800 p-4">
              <p className="text-3xl font-bold">{stats[key]}</p>
              <p className="text-sm text-slate-500 mt-1">{LABELS[key]}</p>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
