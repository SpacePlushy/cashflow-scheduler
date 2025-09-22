"use client";

import { useCallback } from "react";
import { Plan, Deposit, Bill } from "@/lib/types";
import { createDefaultPlan } from "@/lib/defaultPlan";

interface PlanEditorProps {
  plan: Plan;
  onChange: (next: Plan) => void;
}

const fieldClass =
  "w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200";

const sectionClass = "space-y-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm";

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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-900">Plan Builder</h2>
        <button
          type="button"
          onClick={handleReset}
          className="rounded-md border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50"
        >
          Reset to Example
        </button>
      </div>

      <section className={sectionClass}>
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Balances</h3>
        <div className="grid gap-4 md:grid-cols-2">
          <label className="flex flex-col gap-1">
            <span className="text-xs font-medium text-slate-600">Starting Balance ($)</span>
            <input
              type="number"
              step="0.01"
              className={fieldClass}
              value={plan.start_balance}
              onChange={(event) =>
                updatePlan({ start_balance: sanitizeNumber(event.target.value) })
              }
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-xs font-medium text-slate-600">Target End Balance ($)</span>
            <input
              type="number"
              step="0.01"
              className={fieldClass}
              value={plan.target_end}
              onChange={(event) =>
                updatePlan({ target_end: sanitizeNumber(event.target.value) })
              }
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-xs font-medium text-slate-600">Band Width ($)</span>
            <input
              type="number"
              step="0.01"
              className={fieldClass}
              value={plan.band}
              onChange={(event) => updatePlan({ band: sanitizeNumber(event.target.value) })}
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-xs font-medium text-slate-600">Rent Guard ($)</span>
            <input
              type="number"
              step="0.01"
              className={fieldClass}
              value={plan.rent_guard}
              onChange={(event) =>
                updatePlan({ rent_guard: sanitizeNumber(event.target.value) })
              }
            />
          </label>
        </div>
      </section>

      <DepositsEditor
        deposits={plan.deposits}
        onChange={(next) => updatePlan({ deposits: next })}
      />

      <BillsEditor
        bills={plan.bills}
        onChange={(next) => updatePlan({ bills: next })}
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
    <section className={sectionClass}>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Deposits</h3>
        <button
          type="button"
          onClick={handleAdd}
          className="rounded-md border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50"
        >
          Add Deposit
        </button>
      </div>
      <div className="space-y-3">
        {deposits.length === 0 && (
          <p className="text-sm text-slate-500">No deposits set. Add at least one paycheck.</p>
        )}
        {deposits.map((deposit, index) => (
          <div
            key={`${deposit.day}-${index}`}
            className="grid gap-3 rounded-md border border-slate-200 p-3 md:grid-cols-3"
          >
            <label className="flex flex-col gap-1">
              <span className="text-xs font-medium text-slate-600">Day</span>
              <input
                type="number"
                min={1}
                max={30}
                className={fieldClass}
                value={deposit.day}
                onChange={(event) => handleChange(index, "day", event.target.value)}
              />
            </label>
            <label className="flex flex-col gap-1 md:col-span-2">
              <span className="text-xs font-medium text-slate-600">Amount ($)</span>
              <input
                type="number"
                step="0.01"
                className={fieldClass}
                value={deposit.amount}
                onChange={(event) => handleChange(index, "amount", event.target.value)}
              />
            </label>
            <div className="flex items-end justify-end md:col-span-3">
              <button
                type="button"
                onClick={() => handleRemove(index)}
                className="rounded-md border border-red-200 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50"
              >
                Remove
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
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
    <section className={sectionClass}>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Bills</h3>
        <button
          type="button"
          onClick={handleAdd}
          className="rounded-md border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50"
        >
          Add Bill
        </button>
      </div>
      <div className="space-y-3">
        {bills.length === 0 && (
          <p className="text-sm text-slate-500">No bills yet. Add recurring expenses to constrain the solver.</p>
        )}
        {bills.map((bill, index) => (
          <div
            key={`${bill.day}-${bill.name}-${index}`}
            className="grid gap-3 rounded-md border border-slate-200 p-3 md:grid-cols-4"
          >
            <label className="flex flex-col gap-1">
              <span className="text-xs font-medium text-slate-600">Day</span>
              <input
                type="number"
                min={1}
                max={30}
                className={fieldClass}
                value={bill.day}
                onChange={(event) => handleChange(index, "day", event.target.value)}
              />
            </label>
            <label className="flex flex-col gap-1 md:col-span-2">
              <span className="text-xs font-medium text-slate-600">Name</span>
              <input
                type="text"
                className={fieldClass}
                value={bill.name}
                onChange={(event) => handleChange(index, "name", event.target.value)}
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-xs font-medium text-slate-600">Amount ($)</span>
              <input
                type="number"
                step="0.01"
                className={fieldClass}
                value={bill.amount}
                onChange={(event) => handleChange(index, "amount", event.target.value)}
              />
            </label>
            <div className="flex items-end justify-end md:col-span-4">
              <button
                type="button"
                onClick={() => handleRemove(index)}
                className="rounded-md border border-red-200 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50"
              >
                Remove
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
