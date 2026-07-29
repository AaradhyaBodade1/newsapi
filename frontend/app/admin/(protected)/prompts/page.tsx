"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { AIPrompt, Category } from "@/lib/types";

const emptyForm = { name: "", category_id: "", prompt_type: "master", template: "" };

export default function PromptsPage() {
  const [prompts, setPrompts] = useState<AIPrompt[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    const [p, c] = await Promise.all([
      api.get<AIPrompt[]>("/api/v1/prompts"),
      api.get<Category[]>("/api/v1/categories"),
    ]);
    setPrompts(p);
    setCategories(c);
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Failed to load"));
  }, []);

  async function addPrompt(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/api/v1/prompts", {
        name: form.name,
        category_id: form.category_id || null,
        prompt_type: form.prompt_type,
        template: form.template,
      });
      setForm(emptyForm);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add prompt");
    }
  }

  async function toggleActive(prompt: AIPrompt) {
    await api.patch(`/api/v1/prompts/${prompt.id}`, { is_active: !prompt.is_active });
    await load();
  }

  async function remove(id: string) {
    if (!confirm("Delete this prompt?")) return;
    await api.delete(`/api/v1/prompts/${id}`);
    await load();
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">AI prompts</h1>
        <p className="text-sm text-slate-500 mt-1">
          The worker uses the active <code>master</code> prompt for a post&apos;s category if one
          exists, otherwise the global <code>master</code> prompt (category left blank).
        </p>
      </div>
      {error ? <p className="text-red-600 text-sm">{error}</p> : null}

      <form onSubmit={addPrompt} className="flex flex-col gap-3 rounded-lg border border-slate-200 dark:border-slate-800 p-4">
        <div className="flex flex-wrap gap-3">
          <label className="flex flex-col gap-1 text-sm">
            Name
            <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="rounded border border-slate-300 dark:border-slate-700 bg-transparent px-2 py-1.5" />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            Category (optional override)
            <select value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })} className="rounded border border-slate-300 dark:border-slate-700 bg-transparent px-2 py-1.5">
              <option value="">Global (all categories)</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </label>
        </div>
        <label className="flex flex-col gap-1 text-sm">
          Template
          <textarea
            required
            rows={6}
            value={form.template}
            onChange={(e) => setForm({ ...form, template: e.target.value })}
            className="rounded border border-slate-300 dark:border-slate-700 bg-transparent px-2 py-1.5 font-mono text-xs"
          />
        </label>
        <button type="submit" className="self-start rounded bg-brand-600 text-white text-sm px-4 py-2 font-medium hover:bg-brand-700">
          Add prompt
        </button>
      </form>

      <div className="flex flex-col gap-3">
        {prompts.map((p) => (
          <div key={p.id} className="rounded-lg border border-slate-200 dark:border-slate-800 p-4">
            <div className="flex justify-between items-start gap-4">
              <div>
                <p className="font-medium">{p.name}</p>
                <p className="text-xs text-slate-400">
                  {categories.find((c) => c.id === p.category_id)?.name ?? "Global"} · {p.prompt_type}
                </p>
              </div>
              <div className="flex gap-2 shrink-0">
                <button onClick={() => toggleActive(p)} className={`text-xs ${p.is_active ? "text-brand-600" : "text-slate-400"}`}>
                  {p.is_active ? "Active" : "Inactive"}
                </button>
                <button onClick={() => remove(p.id)} className="text-xs text-red-500 hover:underline">Delete</button>
              </div>
            </div>
            <p className="text-xs text-slate-500 mt-2 whitespace-pre-wrap line-clamp-4">{p.template}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
