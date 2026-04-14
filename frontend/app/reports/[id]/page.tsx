"use client";

import { useAuth } from "@clerk/nextjs";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ReportDetail, SectionStatus, getReport } from "@/lib/api";

const SECTION_LABELS: Record<string, string> = {
  offensive_sets: "Offensive Sets",
  defensive_schemes: "Defensive Schemes",
  pnr_coverage: "Pick and Roll Coverage",
  player_pages: "Individual Player Pages",
  game_plan: "Game Plan",
  adjustments_practice: "Adjustments & Practice Plan",
};

const SECTION_ORDER = [
  "offensive_sets",
  "defensive_schemes",
  "pnr_coverage",
  "player_pages",
  "game_plan",
  "adjustments_practice",
];

function ReportStatusBadge({ status }: { status: string }) {
  switch (status) {
    case "pending":
      return (
        <span className="rounded-full bg-gray-800 px-3 py-1 text-xs font-medium text-gray-300">
          Pending
        </span>
      );
    case "processing":
      return (
        <span className="flex items-center gap-1.5 rounded-full bg-orange-900/60 px-3 py-1 text-xs font-medium text-orange-300">
          <svg className="h-3 w-3 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Generating
        </span>
      );
    case "complete":
      return (
        <span className="rounded-full bg-green-900 px-3 py-1 text-xs font-medium text-green-300">
          Complete
        </span>
      );
    case "partial":
      return (
        <span className="rounded-full bg-yellow-900 px-3 py-1 text-xs font-medium text-yellow-300">
          Partial
        </span>
      );
    case "error":
      return (
        <span className="rounded-full bg-red-900 px-3 py-1 text-xs font-medium text-red-300">
          Failed
        </span>
      );
    default:
      return (
        <span className="rounded-full bg-gray-800 px-3 py-1 text-xs font-medium text-gray-300">
          {status}
        </span>
      );
  }
}

function SectionStatusIcon({ status }: { status: string }) {
  switch (status) {
    case "complete":
      return (
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-green-900">
          <svg className="h-3.5 w-3.5 text-green-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </div>
      );
    case "processing":
      return (
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-orange-900/60">
          <svg className="h-3.5 w-3.5 animate-spin text-orange-300" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        </div>
      );
    case "error":
      return (
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-red-900">
          <svg className="h-3.5 w-3.5 text-red-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
      );
    default:
      return (
        <div className="h-6 w-6 rounded-full border-2 border-border" />
      );
  }
}

export default function ReportPage() {
  const { id } = useParams<{ id: string }>();
  const { getToken } = useAuth();

  const [report, setReport] = useState<ReportDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadReport() {
    try {
      const token = await getToken();
      if (!token) return;
      const data = await getReport(token, id);
      setReport(data);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load report");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReport();
  }, [id]);

  // Poll while report is in a non-terminal state (every 10 seconds)
  useEffect(() => {
    if (!report) return;
    if (["complete", "partial", "error"].includes(report.status)) return;

    const interval = setInterval(async () => {
      const token = await getToken();
      if (!token) return;
      try {
        const updated = await getReport(token, id);
        setReport(updated);
      } catch {
        // Polling failure is not critical
      }
    }, 10_000);

    return () => clearInterval(interval);
  }, [report?.status]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-gray-400">Loading report...</p>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-20 text-center">
        <p className="text-gray-400">{error || "Report not found."}</p>
        <a href="/dashboard" className="mt-4 inline-block text-brand">
          Go to Dashboard
        </a>
      </div>
    );
  }

  const sectionMap: Record<string, SectionStatus> = {};
  for (const s of report.sections) {
    sectionMap[s.section_type] = s;
  }

  const completeSections = report.sections.filter((s) => s.status === "complete").length;
  const totalSections = SECTION_ORDER.length;

  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Scouting Report</h1>
          <p className="mt-1 text-sm text-gray-400">
            Created {new Date(report.created_at).toLocaleDateString()}
            {report.generation_time_seconds != null && report.status !== "processing" && (
              <span>
                {" "}
                &middot; Generated in{" "}
                {Math.round(report.generation_time_seconds / 60)} min
              </span>
            )}
          </p>
        </div>
        <ReportStatusBadge status={report.status} />
      </div>

      {/* Error message */}
      {report.error_message && (
        <div className="mt-4 rounded-lg border border-red-800 bg-red-900/20 px-4 py-3">
          <p className="text-sm text-red-300">{report.error_message}</p>
        </div>
      )}

      {/* PDF Download */}
      {report.pdf_url && (
        <a
          href={report.pdf_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-6 flex items-center justify-center gap-2 rounded-lg bg-brand px-6 py-3 text-sm font-semibold text-black hover:bg-orange-400"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Download PDF Report
        </a>
      )}

      {/* Section Progress */}
      <div className="mt-8">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-400">
            Sections
          </h2>
          <span className="text-sm text-gray-400">
            {completeSections} / {totalSections} complete
          </span>
        </div>
        <div className="mt-4 space-y-1">
          {SECTION_ORDER.map((type) => {
            const section = sectionMap[type];
            const status = section?.status || "pending";
            return (
              <div
                key={type}
                className="flex items-center gap-3 rounded-lg border border-border bg-surface px-4 py-3"
              >
                <SectionStatusIcon status={status} />
                <div className="flex-1">
                  <p className="text-sm font-medium text-white">
                    {SECTION_LABELS[type] || type}
                  </p>
                  {section?.model_used && status === "complete" && (
                    <p className="text-xs text-gray-500">
                      {section.model_used}
                      {section.generation_time_seconds != null &&
                        ` \u00b7 ${section.generation_time_seconds}s`}
                    </p>
                  )}
                </div>
                <span
                  className={`text-xs font-medium capitalize ${
                    status === "complete"
                      ? "text-green-400"
                      : status === "processing"
                        ? "text-orange-400"
                        : status === "error"
                          ? "text-red-400"
                          : "text-gray-500"
                  }`}
                >
                  {status}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Back link */}
      <div className="mt-8">
        <a
          href={`/teams/${report.team_id}`}
          className="text-sm text-gray-400 hover:text-white"
        >
          Back to team
        </a>
      </div>
    </div>
  );
}
