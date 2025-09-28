"use client";

import { useMemo, useState } from "react";
import {
  AlertTriangle,
  BadgeCheck,
  CheckCircle2,
  Download,
  Info,
  Loader2,
  ShieldAlert,
} from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ExportFormat, Plan, SolveResponse } from "@/lib/types";
import { exportPlan } from "@/lib/api";

interface ResultsViewProps {
  plan: Plan;
  result: SolveResponse | null;
  status: "idle" | "loading" | "success" | "error";
  error: string | null;
}

const EXPORT_FORMATS: ExportFormat[] = ["md", "csv", "json"];
const NUMERIC_HEAD_CLASS = "text-right";
const NUMERIC_CELL_CLASS = "text-right font-mono tabular-nums";
const ACTION_CELL_CLASS = "text-center font-medium uppercase tracking-wide";

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
});

function formatCurrency(value: string) {
  const parsed = Number(value);
  if (Number.isFinite(parsed)) {
    return currencyFormatter.format(parsed);
  }
  return `$${value}`;
}

export function ResultsView({ plan, result, status, error }: ResultsViewProps) {
  const [downloadStatus, setDownloadStatus] = useState<"idle" | "loading" | "error">(
    "idle",
  );
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const solverSummary = useMemo(() => {
    if (!result) return null;
    return {
      solverName: result.solver.name.toUpperCase(),
      runtime: `${result.solver.seconds.toFixed(2)}s`,
      fallback: result.solver.fallback_reason,
      statuses: result.solver.statuses,
      finalClosing: formatCurrency(result.final_closing),
    };
  }, [result]);

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
      <Card className="border-dashed" id="overview">
        <CardHeader>
          <CardTitle className="text-base font-semibold">Run the solver to see results</CardTitle>
          <CardDescription>
            Configure your plan, then start a solve to inspect ledger details and validation checks.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (status === "loading") {
    return (
      <div className="space-y-4">
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  if (status === "error") {
    return (
      <Alert variant="destructive" className="border border-destructive/40">
        <ShieldAlert className="mt-1" />
        <AlertTitle>Solver failed</AlertTitle>
        <AlertDescription>{error ?? "An unexpected error occurred."}</AlertDescription>
      </Alert>
    );
  }

  if (!result || !solverSummary) {
    return null;
  }

  return (
    <div className="space-y-6" id="verification">
      <Card>
        <CardHeader className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-1">
            <CardTitle className="flex items-center gap-2 text-lg">
              Solver
              <Badge variant="secondary" className="uppercase">
                {solverSummary.solverName}
              </Badge>
            </CardTitle>
            <CardDescription>
              Runtime {solverSummary.runtime}
              {solverSummary.fallback && (
                <span className="ml-2 inline-flex items-center gap-1 text-amber-600 dark:text-amber-400">
                  <AlertTriangle className="size-3" />
                  {solverSummary.fallback}
                </span>
              )}
            </CardDescription>
          </div>
          {solverSummary.statuses.length > 0 && (
            <div className="flex flex-wrap gap-2 text-xs">
              {solverSummary.statuses.map((stage, index) => (
                <Badge key={`${stage}-${index}`} variant="outline" className="uppercase">
                  Stage {index + 1}: {stage}
                </Badge>
              ))}
            </div>
          )}
        </CardHeader>
      </Card>

      <Card id="exports">
        <CardHeader className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-1">
            <CardTitle className="text-lg font-semibold">Solver Output</CardTitle>
            <CardDescription>Final closing balance {solverSummary.finalClosing}</CardDescription>
          </div>
          <div className="flex flex-wrap gap-2">
            {EXPORT_FORMATS.map((format) => (
              <Button
                key={format}
                variant="outline"
                size="sm"
                onClick={() => handleDownload(format)}
                disabled={downloadStatus === "loading"}
              >
                {downloadStatus === "loading" ? (
                  <Loader2 className="mr-2 size-4 animate-spin" />
                ) : (
                  <Download className="mr-2 size-4" />
                )}
                {format.toUpperCase()}
              </Button>
            ))}
          </div>
        </CardHeader>
        {downloadStatus === "error" && downloadError && (
          <CardContent>
            <Alert variant="destructive" className="border border-destructive/40">
              <AlertTitle>Download failed</AlertTitle>
              <AlertDescription>{downloadError}</AlertDescription>
            </Alert>
          </CardContent>
        )}
      </Card>

      <Tabs defaultValue="checks" className="w-full">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <h3 className="text-base font-semibold">Validation & Objective</h3>
            <p className="text-sm text-muted-foreground">
              Cross-check feasibility and inspect the lexicographic objective vector.
            </p>
          </div>
          <TabsList>
            <TabsTrigger value="checks" className="gap-1.5">
              <BadgeCheck className="size-4" /> Checks
            </TabsTrigger>
            <TabsTrigger value="objective" className="gap-1.5">
              <Info className="size-4" /> Objective
            </TabsTrigger>
          </TabsList>
        </div>
        <TabsContent value="checks" className="mt-4">
          <div className="grid gap-3 sm:grid-cols-2">
            {result.checks.map(([label, ok, detail]) => (
              <Card
                key={label}
                className={ok ? "border-emerald-300/60" : "border-destructive/40"}
              >
                <CardHeader className="flex flex-row items-start justify-between gap-2 pb-2">
                  <CardTitle className="text-sm font-medium leading-tight">
                    {label}
                  </CardTitle>
                  {ok ? (
                    <Badge variant="secondary" className="gap-1 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300">
                      <CheckCircle2 className="size-3" />
                      Pass
                    </Badge>
                  ) : (
                    <Badge variant="destructive" className="gap-1">
                      <AlertTriangle className="size-3" />
                      Fail
                    </Badge>
                  )}
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">{detail}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
        <TabsContent value="objective" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Objective Vector</CardTitle>
              <CardDescription>Lower is better; vector compares lexicographic stages.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {result.objective.map((value, index) => (
                  <Badge key={`${value}-${index}`} variant="outline" className="px-3 py-1">
                    Stage {index + 1}: {value}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold">Daily Ledger</CardTitle>
          <CardDescription>
            Each row reflects the validated balance evolution used by the solver and validator.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-hidden rounded-lg border border-border/60 bg-card">
            <Table className="min-w-full">
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[60px] text-center">Day</TableHead>
                  <TableHead className={NUMERIC_HEAD_CLASS}>Opening</TableHead>
                  <TableHead className={NUMERIC_HEAD_CLASS}>Deposits</TableHead>
                  <TableHead className="text-center">Action</TableHead>
                  <TableHead className={NUMERIC_HEAD_CLASS}>Net</TableHead>
                  <TableHead className={NUMERIC_HEAD_CLASS}>Bills</TableHead>
                  <TableHead className={NUMERIC_HEAD_CLASS}>Closing</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {result.ledger.map((row) => (
                  <TableRow key={row.day} className="even:bg-primary/5">
                    <TableCell className="text-center font-medium tabular-nums">
                      {row.day}
                    </TableCell>
                    <TableCell className={NUMERIC_CELL_CLASS}>
                      {formatCurrency(row.opening)}
                    </TableCell>
                    <TableCell className={NUMERIC_CELL_CLASS}>
                      {formatCurrency(row.deposits)}
                    </TableCell>
                    <TableCell className={ACTION_CELL_CLASS}>
                      {(row.action ?? "—").toString()}
                    </TableCell>
                    <TableCell className={NUMERIC_CELL_CLASS}>
                      {formatCurrency(row.net)}
                    </TableCell>
                    <TableCell className={NUMERIC_CELL_CLASS}>
                      {formatCurrency(row.bills)}
                    </TableCell>
                    <TableCell className={`${NUMERIC_CELL_CLASS} font-semibold`}>
                      {formatCurrency(row.closing)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
