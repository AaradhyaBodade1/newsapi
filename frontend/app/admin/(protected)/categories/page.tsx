"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Category } from "@/lib/types";

const emptyForm = { slug: "", name: "", description: "" };

export default function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setCategories(await api.get<Category[]>("/api/v1/categories"));
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Failed to load"));
  }, []);

  async function addCategory(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/api/v1/categories", form);
      setForm(emptyForm);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add category");
    }
  }

  async function toggleActive(category: Category) {
    await api.patch(`/api/v1/categories/${category.id}`, { is_active: !category.is_active });
    await load();
  }

  async function remove(id: string) {
    if (!confirm("Delete this category? Sources/articles referencing it will keep their existing links.")) return;
    await api.delete(`/api/v1/categories/${id}`);
    await load();
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Categories</h1>
        <p className="text-sm text-slate-500 mt-1">These drive the website&apos;s header navigation.</p>
      </div>
      {error ? <p className="text-red-600 text-sm">{error}</p> : null}

      <form onSubmit={addCategory} className="flex flex-wrap gap-3 items-end rounded-lg border border-slate-200 dark:border-slate-800 p-4">
        <label className="flex flex-col gap-1 text-sm">
          Name
          <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="rounded border border-slate-300 dark:border-slate-700 bg-transparent px-2 py-1.5" />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Slug (URL path)
          <input required pattern="[a-z0-9-]+" value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} className="rounded border border-slate-300 dark:border-slate-700 bg-transparent px-2 py-1.5" />
        </label>
        <label className="flex flex-col gap-1 text-sm flex-1 min-w-[240px]">
          Description
          <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="rounded border border-slate-300 dark:border-slate-700 bg-transparent px-2 py-1.5" />
        </label>
        <button type="submit" className="rounded bg-brand-600 text-white text-sm px-4 py-2 font-medium hover:bg-brand-700">
          Add category
        </button>
      </form>

      <div className="overflow-x-auto">
      <table className="w-full min-w-[420px] text-sm border-collapse">
        <thead>
          <tr className="text-left border-b border-slate-200 dark:border-slate-800">
            <th className="py-2 pr-4">Name</th>
            <th className="py-2 pr-4">Slug</th>
            <th className="py-2 pr-4">Active</th>
            <th className="py-2 pr-4" />
          </tr>
        </thead>
        <tbody>
          {categories.map((c) => (
            <tr key={c.id} className="border-b border-slate-100 dark:border-slate-900">
              <td className="py-2 pr-4">{c.name}</td>
              <td className="py-2 pr-4 text-slate-400">/{c.slug}</td>
              <td className="py-2 pr-4">
                <button onClick={() => toggleActive(c)} className={c.is_active ? "text-brand-600" : "text-slate-400"}>
                  {c.is_active ? "Active" : "Inactive"}
                </button>
              </td>
              <td className="py-2 pr-4">
                <button onClick={() => remove(c.id)} className="text-xs text-red-500 hover:underline">Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </div>
  );
}
