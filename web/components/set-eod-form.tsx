"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Schedule, Plan } from "@/lib/types";
import { setEOD, SolverType } from "@/lib/api";
import { Loader2 } from "lucide-react";

interface SetEodFormProps {
  schedule: Schedule;
  plan: Plan;
  onScheduleUpdate: (newSchedule: Schedule) => void;
  solver: SolverType;
}

export function SetEodForm({ schedule, plan, onScheduleUpdate, solver }: SetEodFormProps) {
  const [day, setDay] = useState<number>(15);
  const [targetBalance, setTargetBalance] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Get current EOD balance for selected day
  const currentEod = schedule.ledger[day - 1]?.closing || "0.00";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!targetBalance || isNaN(parseFloat(targetBalance))) {
      setError("Please enter a valid balance amount");
      return;
    }

    if (day < 1 || day > 30) {
      setError("Day must be between 1 and 30");
      return;
    }

    setIsLoading(true);
    try {
      const newSchedule = await setEOD(day, parseFloat(targetBalance), plan, solver);
      onScheduleUpdate(newSchedule);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update schedule");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <p className="text-sm text-muted-foreground mb-4">
        Lock days 1-{day} and adjust the schedule to hit a target balance on day {day}
      </p>
      <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="day">Day</Label>
              <Input
                id="day"
                type="number"
                min={1}
                max={30}
                value={day}
                onChange={(e) => setDay(parseInt(e.target.value) || 1)}
                className="w-full"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="current-eod">Current EOD Balance</Label>
              <Input
                id="current-eod"
                value={`$${currentEod}`}
                disabled
                className="bg-muted"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="target-balance">Target EOD Balance ($)</Label>
            <Input
              id="target-balance"
              type="number"
              step="0.01"
              placeholder="e.g., 500.00"
              value={targetBalance}
              onChange={(e) => setTargetBalance(e.target.value)}
              className="w-full"
            />
          </div>

          {error && (
            <div className="text-sm text-red-500 p-3 rounded-lg bg-red-500/10 border border-red-500/50">
              {error}
            </div>
          )}

          <div className="flex gap-2">
            <Button type="submit" disabled={isLoading} className="flex-1">
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Calculating...
                </>
              ) : (
                "Apply Changes"
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setDay(15);
                setTargetBalance("");
                setError(null);
              }}
            >
              Reset
            </Button>
          </div>

          <div className="text-xs text-muted-foreground p-3 rounded-lg bg-muted/50 border">
            <p className="font-semibold mb-1">How it works:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>Days 1-{day} will be locked with current actions</li>
              <li>A manual adjustment will be added to hit target balance</li>
              <li>Days {day + 1}-30 will be re-optimized</li>
            </ul>
          </div>
        </form>
    </div>
  );
}
