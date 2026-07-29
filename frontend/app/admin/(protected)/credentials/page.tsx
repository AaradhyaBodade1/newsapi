"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface CredentialMeta {
  provider: string;
  key_name: string;
  updated_at: string;
}

const KNOWN_FIELDS: { provider: string; key_name: string; label: string; secret: boolean }[] = [
  { provider: "groq", key_name: "api_key", label: "Groq API key", secret: true },
  { provider: "gemini", key_name: "api_key", label: "Gemini API key (Groq fallback)", secret: true },
  { provider: "unsplash", key_name: "access_key", label: "Unsplash Access Key", secret: true },
  { provider: "smtp", key_name: "host", label: "SMTP host", secret: false },
  { provider: "smtp", key_name: "port", label: "SMTP port", secret: false },
  { provider: "smtp", key_name: "username", label: "SMTP username", secret: false },
  { provider: "smtp", key_name: "password", label: "SMTP password", secret: true },
  { provider: "webhook", key_name: "url", label: "Notification webhook URL", secret: false },
];

export default function CredentialsPage() {
  const [existing, setExisting] = useState<CredentialMeta[]>([]);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setExisting(await api.get<CredentialMeta[]>("/api/v1/credentials"));
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Failed to load"));
  }, []);

  function isConfigured(provider: string, keyName: string) {
    return existing.some((c) => c.provider === provider && c.key_name === keyName);
  }

  async function save(provider: string, keyName: string) {
    const id = `${provider}:${keyName}`;
    const value = drafts[id];
    if (!value) return;
    setSaving(id);
    setError(null);
    try {
      await api.put("/api/v1/credentials", { provider, key_name: keyName, value });
      setDrafts((prev) => ({ ...prev, [id]: "" }));
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save credential");
    } finally {
      setSaving(null);
    }
  }

  return (
    <div className="flex flex-col gap-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold">Credentials</h1>
        <p className="text-sm text-slate-500 mt-1">
          Values are encrypted at rest and never sent back to the browser — only whether a value is
          configured is shown.
        </p>
      </div>
      {error ? <p className="text-red-600 text-sm">{error}</p> : null}

      <div className="flex flex-col gap-3">
        {KNOWN_FIELDS.map((field) => {
          const id = `${field.provider}:${field.key_name}`;
          const configured = isConfigured(field.provider, field.key_name);
          return (
            <div key={id} className="flex items-center justify-between gap-4 text-sm rounded-lg border border-slate-200 dark:border-slate-800 p-4">
              <div>
                <p>{field.label}</p>
                <p className="text-xs text-slate-400">{configured ? "Configured" : "Not set — using .env fallback if present"}</p>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type={field.secret ? "password" : "text"}
                  placeholder={configured ? "•••••••• (replace)" : "value"}
                  value={drafts[id] ?? ""}
                  onChange={(e) => setDrafts((prev) => ({ ...prev, [id]: e.target.value }))}
                  className="rounded border border-slate-300 dark:border-slate-700 bg-transparent px-2 py-1 w-56"
                />
                <button
                  disabled={saving === id}
                  onClick={() => save(field.provider, field.key_name)}
                  className="text-xs rounded bg-brand-600 text-white px-3 py-1.5 font-medium hover:bg-brand-700 disabled:opacity-50"
                >
                  Save
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
