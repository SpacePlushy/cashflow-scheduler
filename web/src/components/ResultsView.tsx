"use client";

import { useState } from "react";
import { ExportFormat, Plan, SolveResponse } from "@/lib/types";
import { exportPlan } from "@/lib/api";

interface ResultsViewProps {
  plan: Plan;
  result: SolveResponse | null;
  status: "idle" | "loading" | "success" | "error";
  error: string | null;
}

const tableClass = "min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-700";
const headerCellClass =
  "bg-slate-50 px-3 py-2 text-left font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300";
const cellClass = "px-3 py-2 text-slate-800 dark:text-slate-200";

export function ResultsView({ plan, result, status, error }: ResultsViewProps) {
  const [downloadStatus, setDownloadStatus] = useState<"idle" | "loading" | "error">("idle");
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const handleDownload = async (format: ExportFormat) => {
    if (!result) return;
    try {
      setDownloadStatus("loading");
      setDownloadError(null);
      const content = await exportPlan(plan, format);
      const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `cashflow_schedule.${format}`;
      anchor.click();
      URL.revokeObjectURL(url);
      setDownloadStatus("idle");
    } catch (err) {
      setDownloadStatus("error");
      setDownloadError(err instanceof Error ? err.message : "Download failed");
    }
  };

  if (status === "idle") {
    return (
      <div className="rounded-lg border border-dashed border-slate-300 p-8 text-center text-slate-500 transition-colors dark:border-slate-700 dark:text-slate-400">
        Configure your plan and run the solver to see results here.
      </div>
    );
  }

  if (status === "loading") {
    return (
      <div className="space-y-4">
        <div className="h-4 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
        <div className="h-4 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
        <div className="h-4 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-300">
        {error ?? "An unexpected error occurred."}
      </div>
    );
  }

  if (!result) {
    return null;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm transition-colors dark:border-slate-700 dark:bg-slate-900 dark:shadow-none">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">
          Solver
        </h3>
        <p className="mt-2 text-sm text-slate-700 dark:text-slate-200">
          Backend: <strong>{result.solver.name.toUpperCase()}</strong>
          {" "}
          ({result.solver.seconds.toFixed(2)}s)
        </p>
        {result.solver.fallback_reason && (
          <p className="mt-1 text-xs text-amber-600 dark:text-amber-400">
            Fallback reason: {result.solver.fallback_reason}
          </p>
        )}
        {result.solver.statuses.length > 0 && (
          <div className="mt-3">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Stage statuses
            </p>
            <ul className="mt-1 grid gap-1 text-xs text-slate-600 dark:text-slate-300">
              {result.solver.statuses.map((stage, idx) => (
                <li key={`${stage}-${idx}`}>Stage {idx + 1}: {stage}</li>
              ))}
            </ul>
          </div>
        )}
      </section>

      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            Solver Output
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-300">
            Final closing balance ${result.final_closing}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {(["md", "csv", "json"] as ExportFormat[]).map((format) => (
            <button
              key={format}
              type="button"
              onClick={() => handleDownload(format)}
              className="rounded-md border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              Download {format.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {downloadStatus === "error" && downloadError && (
        <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-300">
          {downloadError}
        </div>
      )}

      <section className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm transition-colors md:grid-cols-2 dark:border-slate-700 dark:bg-slate-900 dark:shadow-none">
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">
            Objective Vector
          </h3>
          <div className="mt-2 flex flex-wrap gap-2 text-sm text-slate-700 dark:text-slate-200">
            {result.objective.map((value, index) => (
              <span key={index} className="rounded bg-slate-100 px-2 py-1 dark:bg-slate-800">
                {value}
              </span>
            ))}
          </div>
        </div>
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">
            Checks
          </h3>
          <ul className="mt-2 space-y-2 text-sm">
            {result.checks.map(([label, ok, detail]) => (
              <li
                key={label}
                className={`flex flex-col rounded border px-3 py-2 transition ${ok ? "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-200" : "border-red-200 bg-red-50 text-red-700 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-300"}`}
              >
                <span className="font-medium">{label}</span>
                <span className="text-xs opacity-80 dark:text-slate-300">{detail}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm transition-colors dark:border-slate-700 dark:bg-slate-900 dark:shadow-none">
        <table className={tableClass}>
          <thead>
            <tr>
              <th className={headerCellClass}>Day</th>
              <th className={headerCellClass}>Opening</th>
              <th className={headerCellClass}>Deposits</th>
              <th className={headerCellClass}>Action</th>
              <th className={headerCellClass}>Net</th>
              <th className={headerCellClass}>Bills</th>
              <th className={headerCellClass}>Closing</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
            {result.ledger.map((row) => (
              <tr key={row.day}>
                <td className={`${cellClass} font-medium`}>{row.day}</td>
                <td className={cellClass}>${row.opening}</td>
                <td className={cellClass}>${row.deposits}</td>
                <td className={`${cellClass} font-medium`}>{row.action ?? "-"}</td>
                <td className={cellClass}>${row.net}</td>
                <td className={cellClass}>${row.bills}</td>
                <td className={`${cellClass} font-semibold`}>${row.closing}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
