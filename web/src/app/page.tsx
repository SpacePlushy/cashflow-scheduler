"use client";

import { useEffect, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  ClipboardCopy,
  Loader2,
  Sparkles,
} from "lucide-react";

import { AppSidebar } from "@/components/app-sidebar";
import { ModeToggle } from "@/components/mode-toggle";
import { PlanEditor } from "@/components/PlanEditor";
import { ResultsView } from "@/components/ResultsView";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Textarea } from "@/components/ui/textarea";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { Plan, SolveResponse } from "@/lib/types";
import { createDefaultPlan, defaultPlanJson } from "@/lib/defaultPlan";
import { normalizePlan, planToJson } from "@/lib/plan";
import { solvePlan } from "@/lib/api";

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
      setCopyFeedback("Copied to clipboard");
    } catch {
      setCopyFeedback("Copy failed");
    }
  };

  const renderStatusNotice = () => {
    if (status === "loading") {
      return (
        <Alert className="border border-primary/40">
          <Loader2 className="mt-0.5 size-4 animate-spin" />
          <AlertTitle>Solving schedule…</AlertTitle>
          <AlertDescription>
            Running the dynamic programming solver with your latest inputs.
          </AlertDescription>
        </Alert>
      );
    }
    if (status === "error") {
      return (
        <Alert variant="destructive" className="border border-destructive/40">
          <AlertCircle className="mt-0.5 size-4" />
          <AlertTitle>Solver error</AlertTitle>
          <AlertDescription>{error ?? "Failed to solve plan."}</AlertDescription>
        </Alert>
      );
    }
    if (status === "success" && result) {
      return (
        <Alert className="border border-emerald-300/60">
          <CheckCircle2 className="mt-0.5 size-4 text-emerald-600 dark:text-emerald-300" />
          <AlertTitle>Solver finished</AlertTitle>
          <AlertDescription>
            Completed with {result.solver.name.toUpperCase()} in {result.solver.seconds.toFixed(2)}s.
          </AlertDescription>
        </Alert>
      );
    }
    return null;
  };

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <div className="flex min-h-screen flex-col bg-background">
          <header className="border-b border-border/60 bg-background/80 backdrop-blur">
            <div className="flex flex-wrap items-center gap-4 px-6 py-4">
              <div className="flex flex-1 items-center gap-3">
                <SidebarTrigger />
                <div className="flex items-center gap-3">
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                      Cashflow Scheduler
                    </p>
                    <h1 className="text-xl font-semibold leading-tight">Monthly Plan Workbench</h1>
                  </div>
                  <Badge variant="secondary" className="bg-primary/10 text-primary">
                    Beta
                  </Badge>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {status === "success" && result && (
                  <Badge variant="outline" className="gap-1 text-emerald-600 dark:text-emerald-300">
                    <Sparkles className="size-3" />
                    Optimal
                  </Badge>
                )}
                <Button
                  type="button"
                  onClick={handleSolve}
                  disabled={status === "loading"}
                  className="gap-2"
                >
                  {status === "loading" ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <Sparkles className="size-4" />
                  )}
                  Solve Schedule
                </Button>
                <ModeToggle />
              </div>
            </div>
          </header>

          <main className="flex flex-1 flex-col gap-6 px-6 py-6">
            {renderStatusNotice()}

            <div className="grid gap-6 xl:grid-cols-[420px,1fr]">
              <div className="space-y-6">
                <PlanEditor plan={plan} onChange={handlePlanChange} />

                <Card id="plan-json">
                  <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <CardTitle className="text-lg font-semibold">Plan JSON</CardTitle>
                      <CardDescription>Inspect or paste raw plan data to sync with the CLI.</CardDescription>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={handleCopyJson}
                        className="gap-2"
                      >
                        <ClipboardCopy className="size-4" /> Copy JSON
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        onClick={handleApplyJson}
                        disabled={!jsonDirty}
                      >
                        Apply Changes
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <Textarea
                      value={jsonDraft}
                      onChange={(event) => handleJsonChange(event.target.value)}
                      rows={14}
                      spellCheck={false}
                    />
                    <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                      {jsonDirty && <Badge variant="outline">Unsaved edits</Badge>}
                      {copyFeedback && <Badge variant="secondary">{copyFeedback}</Badge>}
                    </div>
                    {jsonError && (
                      <Alert variant="destructive" className="border border-destructive/40">
                        <AlertTitle>Invalid JSON</AlertTitle>
                        <AlertDescription>{jsonError}</AlertDescription>
                      </Alert>
                    )}
                  </CardContent>
                </Card>
              </div>

              <ResultsView plan={plan} result={result} status={status} error={error} />
            </div>
          </main>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
