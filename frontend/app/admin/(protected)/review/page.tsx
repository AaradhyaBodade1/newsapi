"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { api } from "@/lib/api";
import type { GeneratedPost } from "@/lib/types";

export default function ReviewQueuePage() {
  const [posts, setPosts] = useState<GeneratedPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const resp = await api.get<{ items: GeneratedPost[] }>("/api/v1/posts?status=pending_review&limit=50");
      setPosts(resp.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load review queue");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function act(id: string, action: "approve" | "reject") {
    setBusyId(id);
    try {
      await api.post(`/api/v1/posts/${id}/${action}`);
      setPosts((prev) => prev.filter((p) => p.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${action}`);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Review queue</h1>
        <p className="text-sm text-slate-500 mt-1">
          Posts generated from sources/categories with manual approval enabled. Approved posts are
          published on the worker&apos;s next cycle.
        </p>
      </div>
      {error ? <p className="text-red-600 text-sm">{error}</p> : null}
      {loading ? <p className="text-slate-500">Loading…</p> : null}
      {!loading && posts.length === 0 ? <p className="text-slate-500">Nothing waiting for review.</p> : null}
      <div className="flex flex-col gap-4">
        {posts.map((post) => (
          <div key={post.id} className="flex gap-4 rounded-lg border border-slate-200 dark:border-slate-800 p-4">
            {post.image_url ? (
              <div className="relative w-40 h-28 shrink-0 rounded overflow-hidden bg-slate-100 dark:bg-slate-900">
                <Image src={post.image_url} alt="" fill className="object-cover" />
              </div>
            ) : null}
            <div className="flex-1 flex flex-col gap-1">
              <h2 className="font-semibold">{post.headline}</h2>
              <p className="text-sm text-slate-500 line-clamp-2">{post.caption}</p>
              <p className="text-xs text-slate-400">
                Quality score: {post.quality_score ?? "n/a"}
                {post.profanity_flag ? " — profanity flagged" : ""}
              </p>
              <div className="flex gap-2 mt-2">
                <button
                  disabled={busyId === post.id}
                  onClick={() => act(post.id, "approve")}
                  className="rounded bg-brand-600 text-white text-sm px-3 py-1.5 font-medium hover:bg-brand-700 disabled:opacity-50"
                >
                  Approve
                </button>
                <button
                  disabled={busyId === post.id}
                  onClick={() => act(post.id, "reject")}
                  className="rounded border border-slate-300 dark:border-slate-700 text-sm px-3 py-1.5 font-medium hover:bg-slate-100 dark:hover:bg-slate-900 disabled:opacity-50"
                >
                  Reject
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
