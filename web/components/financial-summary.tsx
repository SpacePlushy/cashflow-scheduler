"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Schedule } from "@/lib/types";
import { DollarSign, Calendar, TrendingUp, CheckCircle2, XCircle } from "lucide-react";

interface FinancialSummaryProps {
  schedule: Schedule;
}

export function FinancialSummary({ schedule }: FinancialSummaryProps) {
  const workdays = schedule.objective[0];
  const backToBackPairs = schedule.objective[1];
  const finalDiff = schedule.objective[2];

  // Checks are tuples: [name, ok, detail]
  const allChecksPassed = schedule.checks.every((check) => check[1]);

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Workdays</CardTitle>
          <Calendar className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{workdays}</div>
          <p className="text-xs text-muted-foreground">
            Out of 30 days
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Final Balance</CardTitle>
          <DollarSign className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">${schedule.final_closing}</div>
          <p className="text-xs text-muted-foreground">
            Diff from target: ${(finalDiff / 100).toFixed(2)}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Schedule Quality</CardTitle>
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{backToBackPairs}</div>
          <p className="text-xs text-muted-foreground">
            Back-to-back work pairs
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Validation</CardTitle>
          {allChecksPassed ? (
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          ) : (
            <XCircle className="h-4 w-4 text-red-500" />
          )}
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <Badge variant={allChecksPassed ? "default" : "destructive"}>
              {allChecksPassed ? "All Passed" : "Failed"}
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            {schedule.checks.filter(c => c[1]).length}/{schedule.checks.length} checks
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
