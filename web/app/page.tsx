"use client";

import { useEffect, useState } from "react";
import { FinancialSummary } from "@/components/financial-summary";
import { ScheduleCalendar } from "@/components/schedule-calendar";
import { LedgerTable } from "@/components/ledger-table";
import { ModeToggle } from "@/components/mode-toggle";
import { SetEodForm } from "@/components/set-eod-form";
import { Schedule } from "@/lib/types";
import { solveSchedule } from "@/lib/api";
import { defaultPlan } from "@/lib/defaultPlan";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Loader2, AlertCircle, Calendar as CalendarIcon, ChevronDown, ChevronUp } from "lucide-react";

export default function Home() {
  const [schedule, setSchedule] = useState<Schedule | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSetEodOpen, setIsSetEodOpen] = useState(false);
  const [isLedgerOpen, setIsLedgerOpen] = useState(false);
  const [isValidationOpen, setIsValidationOpen] = useState(true);

  useEffect(() => {
    async function fetchSchedule() {
      try {
        setLoading(true);
        setError(null);
        const result = await solveSchedule(defaultPlan);
        setSchedule(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load schedule");
        console.error("Error fetching schedule:", err);
      } finally {
        setLoading(false);
      }
    }

    fetchSchedule();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-12 w-12 animate-spin text-primary" />
          <p className="text-lg text-muted-foreground">Optimizing your schedule...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <Card className="max-w-md w-full border-destructive">
          <CardContent className="pt-6">
            <div className="flex items-start gap-4">
              <AlertCircle className="h-6 w-6 text-destructive flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="font-semibold text-lg mb-2">Error Loading Schedule</h3>
                <p className="text-sm text-muted-foreground mb-4">{error}</p>
                <Badge variant="destructive">API Connection Failed</Badge>
                <p className="text-xs text-muted-foreground mt-4">
                  Make sure the API server is running at http://localhost:8000
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!schedule) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-muted-foreground">No schedule data available</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b sticky top-0 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CalendarIcon className="h-8 w-8 text-primary" />
            <div>
              <h1 className="text-2xl font-bold">Cashflow Scheduler</h1>
              <p className="text-sm text-muted-foreground">
                30-day optimization with constraint programming
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {schedule.solver && (
              <Badge variant="outline" className="hidden sm:flex">
                Solver: {schedule.solver.name} ({schedule.solver.seconds.toFixed(2)}s)
              </Badge>
            )}
            <ModeToggle />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 space-y-6">
        {/* Financial Summary Cards */}
        <FinancialSummary schedule={schedule} />

        {/* Schedule Calendar */}
        <ScheduleCalendar schedule={schedule} bills={defaultPlan.bills} />

        {/* Set EOD Form */}
        <Collapsible open={isSetEodOpen} onOpenChange={setIsSetEodOpen}>
          <Card>
            <CardHeader className="pb-3">
              <CollapsibleTrigger asChild>
                <Button
                  variant="ghost"
                  className="w-full justify-between p-0 hover:bg-transparent"
                >
                  <CardTitle className="text-lg">Set End-of-Day Balance</CardTitle>
                  {isSetEodOpen ? (
                    <ChevronUp className="h-5 w-5 text-muted-foreground" />
                  ) : (
                    <ChevronDown className="h-5 w-5 text-muted-foreground" />
                  )}
                </Button>
              </CollapsibleTrigger>
            </CardHeader>
            <CollapsibleContent>
              <CardContent className="pt-0">
                <SetEodForm
                  schedule={schedule}
                  plan={defaultPlan}
                  onScheduleUpdate={setSchedule}
                />
              </CardContent>
            </CollapsibleContent>
          </Card>
        </Collapsible>

        {/* Ledger Table */}
        <Collapsible open={isLedgerOpen} onOpenChange={setIsLedgerOpen}>
          <Card>
            <CardHeader className="pb-3">
              <CollapsibleTrigger asChild>
                <Button
                  variant="ghost"
                  className="w-full justify-between p-0 hover:bg-transparent"
                >
                  <CardTitle className="text-lg">Detailed Ledger</CardTitle>
                  {isLedgerOpen ? (
                    <ChevronUp className="h-5 w-5 text-muted-foreground" />
                  ) : (
                    <ChevronDown className="h-5 w-5 text-muted-foreground" />
                  )}
                </Button>
              </CollapsibleTrigger>
            </CardHeader>
            <CollapsibleContent>
              <CardContent className="pt-0">
                <LedgerTable schedule={schedule} />
              </CardContent>
            </CollapsibleContent>
          </Card>
        </Collapsible>

        {/* Validation Details */}
        <Collapsible open={isValidationOpen} onOpenChange={setIsValidationOpen}>
          <Card>
            <CardHeader className="pb-3">
              <CollapsibleTrigger asChild>
                <Button
                  variant="ghost"
                  className="w-full justify-between p-0 hover:bg-transparent"
                >
                  <div className="flex items-center gap-2">
                    <CardTitle className="text-lg">Validation Checks</CardTitle>
                    <Badge
                      variant={schedule.checks.every((c) => c[1]) ? "default" : "destructive"}
                      className="ml-2"
                    >
                      {schedule.checks.filter((c) => c[1]).length}/{schedule.checks.length}
                    </Badge>
                  </div>
                  {isValidationOpen ? (
                    <ChevronUp className="h-5 w-5 text-muted-foreground" />
                  ) : (
                    <ChevronDown className="h-5 w-5 text-muted-foreground" />
                  )}
                </Button>
              </CollapsibleTrigger>
            </CardHeader>
            <CollapsibleContent>
              <CardContent className="pt-0">
                <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-3">
                  {schedule.checks.map((check, idx) => {
                    // Check is a tuple: [name, ok, detail]
                    const [name, ok, detail] = check;
                    return (
                      <div
                        key={idx}
                        className="flex items-start gap-2 p-3 rounded-lg border"
                      >
                        <div
                          className={`h-2 w-2 rounded-full mt-1.5 flex-shrink-0 ${
                            ok ? "bg-green-500" : "bg-red-500"
                          }`}
                        />
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm">{name}</p>
                          <p className="text-xs text-muted-foreground truncate">
                            {detail}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </CollapsibleContent>
          </Card>
        </Collapsible>
      </main>

      {/* Footer */}
      <footer className="border-t mt-12">
        <div className="container mx-auto px-4 py-6 text-center text-sm text-muted-foreground">
          <p>
            Powered by OR-Tools CP-SAT and Dynamic Programming
          </p>
        </div>
      </footer>
    </div>
  );
}
