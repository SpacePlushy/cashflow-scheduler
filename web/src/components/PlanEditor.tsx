"use client";

import { useCallback } from "react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Bill, Deposit, Plan } from "@/lib/types";
import { createDefaultPlan } from "@/lib/defaultPlan";

interface PlanEditorProps {
  plan: Plan;
  onChange: (next: Plan) => void;
}

function sanitizeNumber(value: string): number {
  if (value === "") {
    return 0;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function clampDay(day: number): number {
  if (!Number.isFinite(day)) {
    return 1;
  }
  return Math.min(30, Math.max(1, Math.trunc(day)));
}

export function PlanEditor({ plan, onChange }: PlanEditorProps) {
  const updatePlan = useCallback(
    (partial: Partial<Plan>) => {
      onChange({ ...plan, ...partial });
    },
    [plan, onChange],
  );

  const handleReset = useCallback(() => {
    onChange(createDefaultPlan());
  }, [onChange]);

  return (
    <div className="space-y-6" id="plan">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold tracking-tight">Plan Builder</h2>
          <p className="text-sm text-muted-foreground">
            Adjust balances, deposits, and bills before solving.
          </p>
        </div>
        <Button variant="outline" onClick={handleReset} className="w-fit">
          Reset to Example
        </Button>
      </div>

      <Card>
        <CardHeader className="pb-4">
          <CardTitle>Balances</CardTitle>
          <CardDescription>
            Define guard rails for the dynamic programming solver.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <LabeledNumberField
              label="Starting Balance ($)"
              value={plan.start_balance}
              onChange={(value) => updatePlan({ start_balance: value })}
            />
            <LabeledNumberField
              label="Target End Balance ($)"
              value={plan.target_end}
              onChange={(value) => updatePlan({ target_end: value })}
            />
            <LabeledNumberField
              label="Band Width ($)"
              value={plan.band}
              onChange={(value) => updatePlan({ band: value })}
            />
            <LabeledNumberField
              label="Rent Guard ($)"
              value={plan.rent_guard}
              onChange={(value) => updatePlan({ rent_guard: value })}
            />
          </div>
        </CardContent>
      </Card>

      <DepositsEditor
        deposits={plan.deposits}
        onChange={(next) => updatePlan({ deposits: next })}
      />

      <BillsEditor bills={plan.bills} onChange={(next) => updatePlan({ bills: next })} />
    </div>
  );
}

interface LabeledNumberFieldProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
}

function LabeledNumberField({ label, value, onChange }: LabeledNumberFieldProps) {
  return (
    <div className="space-y-2">
      <Label className="text-xs uppercase tracking-wide text-muted-foreground">
        {label}
      </Label>
      <Input
        type="number"
        step="0.01"
        value={value}
        onChange={(event) => onChange(sanitizeNumber(event.target.value))}
      />
    </div>
  );
}

interface DepositsEditorProps {
  deposits: Deposit[];
  onChange: (next: Deposit[]) => void;
}

function DepositsEditor({ deposits, onChange }: DepositsEditorProps) {
  const handleChange = (index: number, key: keyof Deposit, value: string) => {
    const next = deposits.map((deposit, idx) => {
      if (idx !== index) return deposit;
      if (key === "day") {
        return { ...deposit, day: clampDay(Number(value)) };
      }
      return { ...deposit, amount: sanitizeNumber(value) };
    });
    onChange(next);
  };

  const handleAdd = () => {
    const template: Deposit = { day: 1, amount: 0 };
    onChange([...deposits, template]);
  };

  const handleRemove = (index: number) => {
    onChange(deposits.filter((_, idx) => idx !== index));
  };

  return (
    <Card>
      <CardHeader className="flex flex-col gap-4 pb-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <CardTitle>Deposits</CardTitle>
          <CardDescription>Schedule expected inflows by day of month.</CardDescription>
        </div>
        <Button variant="outline" onClick={handleAdd} className="w-fit">
          Add Deposit
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        {deposits.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No deposits set. Add at least one paycheck.
          </p>
        )}
        {deposits.map((deposit, index) => (
          <div
            key={`${deposit.day}-${index}`}
            className="grid gap-4 rounded-lg border border-border/60 bg-card/60 p-4 transition-colors md:grid-cols-[minmax(0,1fr),minmax(0,1fr),auto]"
          >
            <div className="space-y-2">
              <Label className="text-xs uppercase tracking-wide text-muted-foreground">
                Day
              </Label>
              <Input
                type="number"
                min={1}
                max={30}
                value={deposit.day}
                onChange={(event) => handleChange(index, "day", event.target.value)}
              />
            </div>
            <div className="space-y-2 md:col-span-1">
              <Label className="text-xs uppercase tracking-wide text-muted-foreground">
                Amount ($)
              </Label>
              <Input
                type="number"
                step="0.01"
                value={deposit.amount}
                onChange={(event) => handleChange(index, "amount", event.target.value)}
              />
            </div>
            <div className="flex items-end justify-end">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => handleRemove(index)}
                className="font-medium text-destructive hover:text-destructive"
              >
                Remove
              </Button>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

interface BillsEditorProps {
  bills: Bill[];
  onChange: (next: Bill[]) => void;
}

function BillsEditor({ bills, onChange }: BillsEditorProps) {
  const handleChange = (
    index: number,
    key: keyof Bill,
    value: string,
  ) => {
    const next = bills.map((bill, idx) => {
      if (idx !== index) return bill;
      if (key === "day") {
        return { ...bill, day: clampDay(Number(value)) };
      }
      if (key === "name") {
        return { ...bill, name: value };
      }
      return { ...bill, amount: sanitizeNumber(value) };
    });
    onChange(next);
  };

  const handleAdd = () => {
    const template: Bill = { day: 1, name: "New Bill", amount: 0 };
    onChange([...bills, template]);
  };

  const handleRemove = (index: number) => {
    onChange(bills.filter((_, idx) => idx !== index));
  };

  return (
    <Card>
      <CardHeader className="flex flex-col gap-4 pb-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <CardTitle>Bills</CardTitle>
          <CardDescription>Constrain the schedule with required outflows.</CardDescription>
        </div>
        <Button variant="outline" onClick={handleAdd} className="w-fit">
          Add Bill
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        {bills.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No bills yet. Add recurring expenses to constrain the solver.
          </p>
        )}
        {bills.map((bill, index) => (
          <div
            key={`${bill.day}-${bill.name}-${index}`}
            className="grid gap-4 rounded-lg border border-border/60 bg-card/60 p-4 transition-colors md:grid-cols-[minmax(0,0.5fr),minmax(0,1fr),minmax(0,0.6fr),auto]"
          >
            <div className="space-y-2">
              <Label className="text-xs uppercase tracking-wide text-muted-foreground">
                Day
              </Label>
              <Input
                type="number"
                min={1}
                max={30}
                value={bill.day}
                onChange={(event) => handleChange(index, "day", event.target.value)}
              />
            </div>
            <div className="space-y-2 md:col-span-1">
              <Label className="text-xs uppercase tracking-wide text-muted-foreground">
                Name
              </Label>
              <Input
                type="text"
                value={bill.name}
                onChange={(event) => handleChange(index, "name", event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label className="text-xs uppercase tracking-wide text-muted-foreground">
                Amount ($)
              </Label>
              <Input
                type="number"
                step="0.01"
                value={bill.amount}
                onChange={(event) => handleChange(index, "amount", event.target.value)}
              />
            </div>
            <div className="flex items-end justify-end">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => handleRemove(index)}
                className="font-medium text-destructive hover:text-destructive"
              >
                Remove
              </Button>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
