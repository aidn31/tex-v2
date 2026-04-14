"use client";

import { useAuth } from "@clerk/nextjs";
import { useEffect, useState } from "react";
import { PatternAnalysis, getPatternAnalysis } from "@/lib/api";

const SECTION_LABELS: Record<string, string> = {
  offensive_sets: "Offensive Sets",
  defensive_schemes: "Defensive Schemes",
  pnr_coverage: "PnR Coverage",
  player_pages: "Player Pages",
  game_plan: "Game Plan",
  adjustments_practice: "Adjustments",
};

export default function PatternsPage() {
  const { getToken } = useAuth();
  const [data, setData] = useState<PatternAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [version, setVersion] = useState("");

  async function load() {
    try {
      const token = await getToken();
      if (!token) return;
      const result = await getPatternAnalysis(token, version || undefined);
      setData(result);
    } catch {
      // Non-critical
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [version]);

  if (loading) {
    return <p className="text-gray-400">Loading patterns...</p>;
  }

  if (!data) {
    return <p className="text-gray-400">Failed to load pattern analysis.</p>;
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Pattern Analysis</h2>
        <select
          value={version}
          onChange={(e) => setVersion(e.target.value)}
          className="rounded border border-border bg-background px-2 py-1 text-sm text-white"
        >
          <option value="">All versions</option>
          {data.available_versions.map((v) => (
            <option key={v} value={v}>
              {v}
            </option>
          ))}
        </select>
      </div>

      {/* Summary stats */}
      <div className="mt-4 grid grid-cols-3 gap-4">
        <div className="rounded-lg border border-border bg-surface p-4 text-center">
          <p className="text-2xl font-bold text-white">
            {data.total_corrections}
          </p>
          <p className="text-xs text-gray-400">Total Corrections</p>
        </div>
        <div className="rounded-lg border border-border bg-surface p-4 text-center">
          <p className="text-2xl font-bold text-red-400">
            {data.total_errors}
          </p>
          <p className="text-xs text-gray-400">Errors Found</p>
        </div>
        <div className="rounded-lg border border-border bg-surface p-4 text-center">
          <p className="text-2xl font-bold text-brand">
            {data.total_corrections > 0
              ? (
                  (100 * (data.total_corrections - data.total_errors)) /
                  data.total_corrections
                ).toFixed(1)
              : "—"}
            %
          </p>
          <p className="text-xs text-gray-400">Accuracy Rate</p>
        </div>
      </div>

      {/* Error rate by category */}
      <h3 className="mt-8 text-sm font-semibold uppercase tracking-wider text-gray-400">
        By Category
      </h3>
      {data.by_category.length === 0 ? (
        <p className="mt-2 text-gray-500">No data yet.</p>
      ) : (
        <table className="mt-3 w-full text-left text-sm">
          <thead>
            <tr className="border-b border-border text-gray-400">
              <th className="pb-2 pr-4">Category</th>
              <th className="pb-2 pr-4 text-right">Total</th>
              <th className="pb-2 pr-4 text-right">Errors</th>
              <th className="pb-2 text-right">Error Rate</th>
            </tr>
          </thead>
          <tbody>
            {data.by_category.map((row) => (
              <tr key={row.category} className="border-b border-border/50">
                <td className="py-2 pr-4 text-white">{row.category}</td>
                <td className="py-2 pr-4 text-right text-gray-300">
                  {row.total}
                </td>
                <td className="py-2 pr-4 text-right text-gray-300">
                  {row.errors}
                </td>
                <td className="py-2 text-right">
                  <span
                    className={`font-medium ${
                      row.error_rate > 20
                        ? "text-red-400"
                        : row.error_rate > 10
                          ? "text-yellow-400"
                          : "text-green-400"
                    }`}
                  >
                    {row.error_rate}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Error rate by section */}
      <h3 className="mt-8 text-sm font-semibold uppercase tracking-wider text-gray-400">
        By Section
      </h3>
      {data.by_section.length === 0 ? (
        <p className="mt-2 text-gray-500">No data yet.</p>
      ) : (
        <table className="mt-3 w-full text-left text-sm">
          <thead>
            <tr className="border-b border-border text-gray-400">
              <th className="pb-2 pr-4">Section</th>
              <th className="pb-2 pr-4 text-right">Total</th>
              <th className="pb-2 pr-4 text-right">Errors</th>
              <th className="pb-2 text-right">Error Rate</th>
            </tr>
          </thead>
          <tbody>
            {data.by_section.map((row) => (
              <tr key={row.section_type} className="border-b border-border/50">
                <td className="py-2 pr-4 text-white">
                  {SECTION_LABELS[row.section_type] || row.section_type}
                </td>
                <td className="py-2 pr-4 text-right text-gray-300">
                  {row.total}
                </td>
                <td className="py-2 pr-4 text-right text-gray-300">
                  {row.errors}
                </td>
                <td className="py-2 text-right">
                  <span
                    className={`font-medium ${
                      row.error_rate > 20
                        ? "text-red-400"
                        : row.error_rate > 10
                          ? "text-yellow-400"
                          : "text-green-400"
                    }`}
                  >
                    {row.error_rate}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
