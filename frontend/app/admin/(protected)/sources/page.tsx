"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Category, Source } from "@/lib/types";

const emptyForm = { name: "", type: "rss" as "rss" | "api", url: "", category_id: "", manual_approval: false };

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    const [s, c] = await Promise.all([
      api.get<Source[]>("/api/v1/sources"),
      api.get<Category[]>("/api/v1/categories"),
    ]);
    setSources(s);
    setCategories(c);
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Failed to load"));
  }, []);

  async function addSource(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/api/v1/sources", {
        name: form.name,
        type: form.type,
        url: form.url,
        category_id: form.category_id || null,
        manual_approval: form.manual_approval,
      });
      setForm(emptyForm);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add source");
    }
  }

  async function toggleActive(source: Source) {
    await api.patch(`/api/v1/sources/${source.id}`, { is_active: !source.is_active });
    await load();
  }

  async function remove(id: string) {
    if (!confirm("Delete this source?")) return;
    await api.delete(`/api/v1/sources/${id}`);
    await load();
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold">Sources</h1>
      {error ? <p className="text-red-600 text-sm">{error}</p> : null}

      <form onSubmit={addSource} className="flex flex-wrap gap-3 items-end rounded-lg border border-slate-200 dark:border-slate-800 p-4">
        <label className="flex flex-col gap-1 text-sm">
          Name
          <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="rounded border border-slate-300 dark:border-slate-700 bg-transparent px-2 py-1.5" />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Type
          <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value as "rss" | "api" })} className="rounded border border-slate-300 dark:border-slate-700 bg-transparent px-2 py-1.5">
            <option value="rss">RSS</option>
            <option value="api">API</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm flex-1 min-w-[240px]">
          Feed/API URL
          <input required type="url" value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} className="rounded border border-slate-300 dark:border-slate-700 bg-transparent px-2 py-1.5" />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Category
          <select value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })} className="rounded border border-slate-300 dark:border-slate-700 bg-transparent px-2 py-1.5">
            <option value="">None</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={form.manual_approval} onChange={(e) => setForm({ ...form, manual_approval: e.target.checked })} />
          Require manual approval
        </label>
        <button type="submit" className="rounded bg-brand-600 text-white text-sm px-4 py-2 font-medium hover:bg-brand-700">
          Add source
        </button>
      </form>

      <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] text-sm border-collapse">
        <thead>
          <tr className="text-left border-b border-slate-200 dark:border-slate-800">
            <th className="py-2 pr-4">Name</th>
            <th className="py-2 pr-4">Type</th>
            <th className="py-2 pr-4">Category</th>
            <th className="py-2 pr-4">Active</th>
            <th className="py-2 pr-4">Last fetched</th>
            <th className="py-2 pr-4">Last error</th>
            <th className="py-2 pr-4" />
          </tr>
        </thead>
        <tbody>
          {sources.map((s) => (
            <tr key={s.id} className="border-b border-slate-100 dark:border-slate-900">
              <td className="py-2 pr-4">{s.name}</td>
              <td className="py-2 pr-4 uppercase text-xs">{s.type}</td>
              <td className="py-2 pr-4">{categories.find((c) => c.id === s.category_id)?.name ?? "—"}</td>
              <td className="py-2 pr-4">
                <button onClick={() => toggleActive(s)} className={s.is_active ? "text-brand-600" : "text-slate-400"}>
                  {s.is_active ? "Active" : "Inactive"}
                </button>
              </td>
              <td className="py-2 pr-4 text-xs text-slate-400">{s.last_fetched_at ? new Date(s.last_fetched_at).toLocaleString("en-US") : "never"}</td>
              <td className="py-2 pr-4 text-xs text-red-500 max-w-[200px] truncate" title={s.last_error ?? ""}>{s.last_error ?? ""}</td>
              <td className="py-2 pr-4">
                <button onClick={() => remove(s.id)} className="text-xs text-red-500 hover:underline">Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </div>
  );
}
