"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type SettingsMap = Record<string, unknown>;

const FIELD_LABELS: Record<string, string> = {
  posting_frequency_minutes: "Posting frequency (minutes) — informational; set the actual cron schedule on the worker host",
  manual_approval_default: "Require manual approval by default",
  max_retry_attempts: "Max publish retry attempts",
  max_articles_per_run: "Max new articles processed per cycle",
  quality_score_threshold: "Minimum AI quality score to auto-approve (0-1)",
  notification_email: "Failed-job notification email",
  notification_webhook_url: "Failed-job notification webhook URL",
};

export default function SettingsPage() {
  const [settings, setSettings] = useState<SettingsMap>({});
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setSettings(await api.get<SettingsMap>("/api/v1/settings"));
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Failed to load"));
  }, []);

  async function save(key: string, value: unknown) {
    setSaving(key);
    setError(null);
    try {
      await api.put(`/api/v1/settings/${key}`, { value });
      setSettings((prev) => ({ ...prev, [key]: value }));
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to save ${key}`);
    } finally {
      setSaving(null);
    }
  }

  return (
    <div className="flex flex-col gap-6 max-w-2xl">
      <h1 className="text-2xl font-bold">Settings</h1>
      {error ? <p className="text-red-600 text-sm">{error}</p> : null}
      <div className="flex flex-col gap-4">
        {Object.entries(FIELD_LABELS).map(([key, label]) => (
          <SettingField
            key={key}
            label={label}
            value={settings[key]}
            saving={saving === key}
            onSave={(value) => save(key, value)}
          />
        ))}
      </div>
    </div>
  );
}

function SettingField({
  label,
  value,
  saving,
  onSave,
}: {
  label: string;
  value: unknown;
  saving: boolean;
  onSave: (value: unknown) => void;
}) {
  const isBoolean = typeof value === "boolean";
  const [draft, setDraft] = useState(value);

  useEffect(() => setDraft(value), [value]);

  if (isBoolean) {
    return (
      <label className="flex items-center justify-between gap-4 text-sm rounded-lg border border-slate-200 dark:border-slate-800 p-4">
        <span>{label}</span>
        <input
          type="checkbox"
          checked={Boolean(draft)}
          onChange={(e) => onSave(e.target.checked)}
          disabled={saving}
        />
      </label>
    );
  }

  return (
    <div className="flex items-center justify-between gap-4 text-sm rounded-lg border border-slate-200 dark:border-slate-800 p-4">
      <span>{label}</span>
      <div className="flex items-center gap-2">
        <input
          value={String(draft ?? "")}
          onChange={(e) => setDraft(e.target.value)}
          className="rounded border border-slate-300 dark:border-slate-700 bg-transparent px-2 py-1 w-40"
        />
        <button
          disabled={saving}
          onClick={() => onSave(typeof value === "number" ? Number(draft) : draft)}
          className="text-xs rounded bg-brand-600 text-white px-3 py-1.5 font-medium hover:bg-brand-700 disabled:opacity-50"
        >
          Save
        </button>
      </div>
    </div>
  );
}
