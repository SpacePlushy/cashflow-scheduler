"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { FinancialSummary } from "@/components/financial-summary";
import { ScheduleCalendar } from "@/components/schedule-calendar";
import { LedgerTable } from "@/components/ledger-table";
import { ModeToggle } from "@/components/mode-toggle";
import { SetEodForm } from "@/components/set-eod-form";
import { Schedule } from "@/lib/types";
import { solveSchedule, SolverType } from "@/lib/api";
import { defaultPlan } from "@/lib/defaultPlan";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Loader2, AlertCircle, Calendar as CalendarIcon, ChevronDown, ChevronUp, RefreshCw } from "lucide-react";

export default function Home() {
  const [schedule, setSchedule] = useState<Schedule | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isResolving, setIsResolving] = useState(false);
  const [isSetEodOpen, setIsSetEodOpen] = useState(false);
  const [isLedgerOpen, setIsLedgerOpen] = useState(false);
  const [isValidationOpen, setIsValidationOpen] = useState(true);
  const [solver, setSolver] = useState<SolverType>("cpsat");

  useEffect(() => {
    async function fetchSchedule() {
      try {
        setLoading(true);
        setError(null);
        const result = await solveSchedule(defaultPlan, solver);
        setSchedule(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load schedule");
        console.error("Error fetching schedule:", err);
      } finally {
        setLoading(false);
      }
    }

    fetchSchedule();
  }, [solver]);

  const handleResolve = async () => {
    try {
      setIsResolving(true);
      setError(null);
      const result = await solveSchedule(defaultPlan, solver);
      setSchedule(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to resolve schedule");
      console.error("Error resolving schedule:", err);
    } finally {
      setIsResolving(false);
    }
  };

  if (loading) {
    return (
      <motion.div
        className="min-h-screen flex items-center justify-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        <motion.div
          className="flex flex-col items-center gap-4"
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <motion.div
            animate={{
              rotate: 360,
              scale: [1, 1.1, 1]
            }}
            transition={{
              rotate: { duration: 1, repeat: Infinity, ease: "linear" },
              scale: { duration: 1.5, repeat: Infinity, ease: "easeInOut" }
            }}
          >
            <Loader2 className="h-12 w-12 text-primary" />
          </motion.div>
          <motion.p
            className="text-lg text-muted-foreground"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            Optimizing your schedule...
          </motion.p>
        </motion.div>
      </motion.div>
    );
  }

  if (error) {
    return (
      <motion.div
        className="min-h-screen flex items-center justify-center p-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4 }}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0, y: 20 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          transition={{ type: "spring", stiffness: 200, damping: 20 }}
        >
          <Card className="max-w-md w-full border-destructive">
            <CardContent className="pt-6">
              <div className="flex items-start gap-4">
                <motion.div
                  animate={{ rotate: [0, -10, 10, -10, 0] }}
                  transition={{ duration: 0.5, delay: 0.2 }}
                >
                  <AlertCircle className="h-6 w-6 text-destructive flex-shrink-0 mt-0.5" />
                </motion.div>
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
        </motion.div>
      </motion.div>
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
      {/* Header - Mobile Optimized */}
      <motion.header
        className="border-b sticky top-0 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 z-50"
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      >
        <div className="container mx-auto px-3 sm:px-4 py-3 sm:py-4">
          {/* Mobile: Stacked Layout */}
          <div className="flex flex-col gap-3 md:hidden">
            {/* Top Row: Logo, Title, Theme */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CalendarIcon className="h-6 w-6 text-primary" />
                <div>
                  <h1 className="text-lg font-bold">Cashflow Scheduler</h1>
                  <p className="text-xs text-muted-foreground">
                    30-day optimization
                  </p>
                </div>
              </div>
              <ModeToggle />
            </div>

            {/* Bottom Row: Solver Controls */}
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 border rounded-md p-0.5 flex-1">
                <Button
                  onClick={() => setSolver("cpsat")}
                  variant={solver === "cpsat" ? "default" : "ghost"}
                  size="sm"
                  className="h-7 flex-1 text-xs"
                >
                  CP-SAT
                </Button>
                <Button
                  onClick={() => setSolver("dp")}
                  variant={solver === "dp" ? "default" : "ghost"}
                  size="sm"
                  className="h-7 flex-1 text-xs"
                >
                  DP
                </Button>
              </div>
              <Button
                onClick={handleResolve}
                disabled={isResolving}
                variant="outline"
                size="sm"
                className="gap-1.5 h-7"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${isResolving ? 'animate-spin' : ''}`} />
                <span className="text-xs">{isResolving ? 'Solving' : 'Re-run'}</span>
              </Button>
            </div>

            {/* Solver Info Badge */}
            {schedule.solver && (
              <Badge variant="outline" className="w-fit text-xs">
                {schedule.solver.name} • {schedule.solver.seconds.toFixed(2)}s
              </Badge>
            )}
          </div>

          {/* Desktop: Original Layout */}
          <div className="hidden md:flex items-center justify-between">
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
                <Badge variant="outline">
                  Solver: {schedule.solver.name} ({schedule.solver.seconds.toFixed(2)}s)
                </Badge>
              )}
              <div className="flex items-center gap-2 border rounded-md p-1">
                <Button
                  onClick={() => setSolver("cpsat")}
                  variant={solver === "cpsat" ? "default" : "ghost"}
                  size="sm"
                  className="h-8"
                >
                  CP-SAT
                </Button>
                <Button
                  onClick={() => setSolver("dp")}
                  variant={solver === "dp" ? "default" : "ghost"}
                  size="sm"
                  className="h-8"
                >
                  DP
                </Button>
              </div>
              <Button
                onClick={handleResolve}
                disabled={isResolving}
                variant="outline"
                size="sm"
                className="gap-2"
              >
                <RefreshCw className={`h-4 w-4 ${isResolving ? 'animate-spin' : ''}`} />
                {isResolving ? 'Solving...' : 'Re-run Solver'}
              </Button>
              <ModeToggle />
            </div>
          </div>
        </div>
      </motion.header>

      {/* Main Content */}
      <main className="container mx-auto px-3 sm:px-4 py-4 sm:py-6 md:py-8 space-y-4 sm:space-y-6">
        {/* Financial Summary Cards */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <FinancialSummary schedule={schedule} />
        </motion.div>

        {/* Schedule Calendar */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          <ScheduleCalendar schedule={schedule} bills={defaultPlan.bills} />
        </motion.div>

        {/* Set EOD Form */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5 }}
        >
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
                  solver={solver}
                />
              </CardContent>
            </CollapsibleContent>
          </Card>
        </Collapsible>
        </motion.div>

        {/* Ledger Table */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6 }}
        >
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
        </motion.div>

        {/* Validation Details */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.7 }}
        >
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
        </motion.div>
      </main>

      {/* Footer */}
      <motion.footer
        className="border-t mt-12"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 0.8 }}
      >
        <div className="container mx-auto px-4 py-6 text-center text-sm text-muted-foreground">
          <p>
            Powered by OR-Tools CP-SAT and Dynamic Programming
          </p>
          <p className="mt-2">
            made with ❤️ by Frankie
          </p>
        </div>
      </motion.footer>
    </div>
  );
}
