"use client";

import { useEffect, useState } from "react";
import { Plan, SolveResponse } from "@/lib/types";
import { createDefaultPlan, defaultPlanJson } from "@/lib/defaultPlan";
import { normalizePlan, planToJson } from "@/lib/plan";
import { solvePlan } from "@/lib/api";
import { PlanEditor } from "@/components/PlanEditor";
import { ResultsView } from "@/components/ResultsView";

export default function Home() {
  const [plan, setPlan] = useState<Plan>(() => createDefaultPlan());
  const [result, setResult] = useState<SolveResponse | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  const [jsonDraft, setJsonDraft] = useState(defaultPlanJson);
  const [jsonDirty, setJsonDirty] = useState(false);
  const [jsonError, setJsonError] = useState<string | null>(null);
  const [copyFeedback, setCopyFeedback] = useState<string | null>(null);

  useEffect(() => {
    if (!jsonDirty) {
      setJsonDraft(planToJson(plan));
    }
  }, [plan, jsonDirty]);

  const handlePlanChange = (next: Plan) => {
    setPlan(next);
    setResult(null);
    setStatus("idle");
  };

  const handleSolve = async () => {
    setStatus("loading");
    setError(null);
    try {
      const response = await solvePlan(plan);
      setResult(response);
      setStatus("success");
    } catch (err) {
      setStatus("error");
      setError(err instanceof Error ? err.message : "Failed to solve plan");
    }
  };

  const handleJsonChange = (value: string) => {
    setJsonDirty(true);
    setJsonDraft(value);
    setJsonError(null);
    setCopyFeedback(null);
  };

  const handleApplyJson = () => {
    try {
      const parsed = normalizePlan(JSON.parse(jsonDraft));
      setPlan(parsed);
      setResult(null);
      setStatus("idle");
      setJsonDirty(false);
      setJsonError(null);
    } catch (err) {
      setJsonError(err instanceof Error ? err.message : "Invalid plan JSON");
    }
  };

  const handleCopyJson = async () => {
    try {
      await navigator.clipboard.writeText(jsonDraft);
      setCopyFeedback("Copied!");
    } catch {
      setCopyFeedback("Copy failed");
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 py-10 dark:bg-slate-950">
      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-4">
        <header className="flex flex-col gap-4 rounded-xl bg-white p-6 shadow-sm transition-colors sm:flex-row sm:items-end sm:justify-between dark:bg-slate-900 dark:shadow-none">
          <div className="space-y-1">
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-500 dark:text-blue-300">
              Cashflow Scheduler
            </p>
            <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
              Build your monthly plan and run the solver without the CLI
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-300">
              Adjust deposits, bills, and guard rails, then solve to see the optimal shift
              schedule and validation checks instantly.
            </p>
          </div>
          <button
            type="button"
            onClick={handleSolve}
            disabled={status === "loading"}
            className="inline-flex h-11 items-center justify-center rounded-md bg-blue-600 px-5 text-sm font-medium text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300 dark:hover:bg-blue-500"
          >
            {status === "loading" ? "Solving…" : "Solve Schedule"}
          </button>
        </header>

        <div className="grid gap-8 lg:grid-cols-[420px,1fr]">
          <div className="space-y-6">
            <PlanEditor plan={plan} onChange={handlePlanChange} />

            <section className="space-y-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm transition-colors dark:border-slate-700 dark:bg-slate-900 dark:shadow-none">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">
                  Plan JSON
                </h3>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={handleCopyJson}
                    className="rounded-md border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
                  >
                    Copy JSON
                  </button>
                  <button
                    type="button"
                    onClick={handleApplyJson}
                    className="rounded-md border border-blue-200 bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700 shadow-sm transition hover:bg-blue-100 dark:border-blue-500/40 dark:bg-blue-500/10 dark:text-blue-200 dark:hover:bg-blue-500/20"
                  >
                    Apply Changes
                  </button>
                </div>
              </div>
              <textarea
                value={jsonDraft}
                onChange={(event) => handleJsonChange(event.target.value)}
                rows={12}
                spellCheck={false}
                className="w-full rounded-md border border-slate-300 bg-slate-50 p-3 font-mono text-xs leading-5 text-slate-800 transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:border-blue-400 dark:focus:ring-blue-500/30"
              />
              {jsonError && (
                <p className="text-sm text-red-500 dark:text-red-400">{jsonError}</p>
              )}
              {copyFeedback && (
                <p className="text-xs text-slate-500 dark:text-slate-400">{copyFeedback}</p>
              )}
            </section>
          </div>

          <ResultsView plan={plan} result={result} status={status} error={error} />
        </div>
      </div>
    </div>
  );
}
