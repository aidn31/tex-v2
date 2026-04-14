"use client";

import { useAuth } from "@clerk/nextjs";
import { useEffect, useState } from "react";
import {
  Correction,
  createCorrection,
  listCorrections,
} from "@/lib/api";

const SECTION_TYPES = [
  "offensive_sets",
  "defensive_schemes",
  "pnr_coverage",
  "player_pages",
  "game_plan",
  "adjustments_practice",
];

const CATEGORIES = [
  "set_identification",
  "player_attribution",
  "frequency_count",
  "tendency",
  "coverage_type",
  "personnel_evaluation",
  "strategic_reasoning",
];

export default function AdminCorrectionsPage() {
  const { getToken } = useAuth();
  const [corrections, setCorrections] = useState<Correction[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [filterSection, setFilterSection] = useState("");
  const [filterCategory, setFilterCategory] = useState("");
  const [filterCorrect, setFilterCorrect] = useState<string>("");

  // New correction form
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    report_id: "",
    film_id: "",
    section_type: "offensive_sets",
    ai_claim: "",
    is_correct: true,
    correct_claim: "",
    category: "set_identification",
    confidence: "high",
    prompt_version: "v1.0",
    admin_notes: "",
  });
  const [saving, setSaving] = useState(false);

  async function loadCorrections() {
    try {
      const token = await getToken();
      if (!token) return;
      const params: Record<string, string | boolean> = {};
      if (filterSection) params.section_type = filterSection;
      if (filterCategory) params.category = filterCategory;
      if (filterCorrect !== "") params.is_correct = filterCorrect === "true";
      const data = await listCorrections(token, params);
      setCorrections(data.corrections);
      setTotal(data.total);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load corrections");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCorrections();
  }, [filterSection, filterCategory, filterCorrect]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const token = await getToken();
      if (!token) return;
      await createCorrection(token, {
        ...formData,
        correct_claim: formData.is_correct ? undefined : formData.correct_claim,
        admin_notes: formData.admin_notes || undefined,
      });
      setShowForm(false);
      setFormData({
        report_id: "",
        film_id: "",
        section_type: "offensive_sets",
        ai_claim: "",
        is_correct: true,
        correct_claim: "",
        category: "set_identification",
        confidence: "high",
        prompt_version: "v1.0",
        admin_notes: "",
      });
      await loadCorrections();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save correction");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <p className="text-gray-400">Loading corrections...</p>;
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">
          Corrections ({total})
        </h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="rounded bg-brand px-3 py-1.5 text-sm font-semibold text-black hover:bg-orange-400"
        >
          {showForm ? "Cancel" : "New Correction"}
        </button>
      </div>

      {error && (
        <p className="mt-3 rounded bg-red-900/50 px-4 py-2 text-sm text-red-300">
          {error}
        </p>
      )}

      {/* New correction form */}
      {showForm && (
        <form
          onSubmit={handleSave}
          className="mt-4 space-y-3 rounded-lg border border-border bg-surface p-4"
        >
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-400">Report ID</label>
              <input
                value={formData.report_id}
                onChange={(e) =>
                  setFormData({ ...formData, report_id: e.target.value })
                }
                className="mt-1 w-full rounded border border-border bg-background px-2 py-1 text-sm text-white"
                required
              />
            </div>
            <div>
              <label className="block text-xs text-gray-400">Film ID</label>
              <input
                value={formData.film_id}
                onChange={(e) =>
                  setFormData({ ...formData, film_id: e.target.value })
                }
                className="mt-1 w-full rounded border border-border bg-background px-2 py-1 text-sm text-white"
                required
              />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs text-gray-400">Section</label>
              <select
                value={formData.section_type}
                onChange={(e) =>
                  setFormData({ ...formData, section_type: e.target.value })
                }
                className="mt-1 w-full rounded border border-border bg-background px-2 py-1 text-sm text-white"
              >
                {SECTION_TYPES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-400">Category</label>
              <select
                value={formData.category}
                onChange={(e) =>
                  setFormData({ ...formData, category: e.target.value })
                }
                className="mt-1 w-full rounded border border-border bg-background px-2 py-1 text-sm text-white"
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-400">Confidence</label>
              <select
                value={formData.confidence}
                onChange={(e) =>
                  setFormData({ ...formData, confidence: e.target.value })
                }
                className="mt-1 w-full rounded border border-border bg-background px-2 py-1 text-sm text-white"
              >
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs text-gray-400">AI Claim</label>
            <textarea
              value={formData.ai_claim}
              onChange={(e) =>
                setFormData({ ...formData, ai_claim: e.target.value })
              }
              className="mt-1 w-full rounded border border-border bg-background px-2 py-1 text-sm text-white"
              rows={2}
              required
            />
          </div>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm text-white">
              <input
                type="radio"
                checked={formData.is_correct}
                onChange={() =>
                  setFormData({ ...formData, is_correct: true })
                }
              />
              Correct
            </label>
            <label className="flex items-center gap-2 text-sm text-white">
              <input
                type="radio"
                checked={!formData.is_correct}
                onChange={() =>
                  setFormData({ ...formData, is_correct: false })
                }
              />
              Incorrect
            </label>
          </div>
          {!formData.is_correct && (
            <div>
              <label className="block text-xs text-gray-400">
                Correct Claim
              </label>
              <textarea
                value={formData.correct_claim}
                onChange={(e) =>
                  setFormData({ ...formData, correct_claim: e.target.value })
                }
                className="mt-1 w-full rounded border border-border bg-background px-2 py-1 text-sm text-white"
                rows={2}
                required
              />
            </div>
          )}
          <div>
            <label className="block text-xs text-gray-400">
              Notes (optional)
            </label>
            <input
              value={formData.admin_notes}
              onChange={(e) =>
                setFormData({ ...formData, admin_notes: e.target.value })
              }
              className="mt-1 w-full rounded border border-border bg-background px-2 py-1 text-sm text-white"
            />
          </div>
          <button
            type="submit"
            disabled={saving}
            className="rounded bg-brand px-4 py-1.5 text-sm font-semibold text-black hover:bg-orange-400 disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save Correction"}
          </button>
        </form>
      )}

      {/* Filters */}
      <div className="mt-4 flex gap-3">
        <select
          value={filterSection}
          onChange={(e) => setFilterSection(e.target.value)}
          className="rounded border border-border bg-background px-2 py-1 text-sm text-white"
        >
          <option value="">All sections</option>
          {SECTION_TYPES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value)}
          className="rounded border border-border bg-background px-2 py-1 text-sm text-white"
        >
          <option value="">All categories</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <select
          value={filterCorrect}
          onChange={(e) => setFilterCorrect(e.target.value)}
          className="rounded border border-border bg-background px-2 py-1 text-sm text-white"
        >
          <option value="">All</option>
          <option value="true">Correct</option>
          <option value="false">Incorrect</option>
        </select>
      </div>

      {/* Corrections list */}
      <div className="mt-4 space-y-2">
        {corrections.length === 0 && (
          <p className="text-gray-400">No corrections yet.</p>
        )}
        {corrections.map((c) => (
          <div
            key={c.id}
            className="rounded-lg border border-border bg-surface px-4 py-3"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm text-white">{c.ai_claim}</p>
                {!c.is_correct && c.correct_claim && (
                  <p className="mt-1 text-sm text-green-400">
                    Correction: {c.correct_claim}
                  </p>
                )}
              </div>
              <span
                className={`ml-3 shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${
                  c.is_correct
                    ? "bg-green-900 text-green-300"
                    : "bg-red-900 text-red-300"
                }`}
              >
                {c.is_correct ? "Correct" : "Incorrect"}
              </span>
            </div>
            <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-500">
              <span>{c.section_type}</span>
              <span>&middot;</span>
              <span>{c.category}</span>
              <span>&middot;</span>
              <span>{c.prompt_version}</span>
              <span>&middot;</span>
              <span>{c.confidence}</span>
              {c.admin_notes && (
                <>
                  <span>&middot;</span>
                  <span className="text-gray-400">{c.admin_notes}</span>
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
