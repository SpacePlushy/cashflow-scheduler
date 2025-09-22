import { Plan, PlanAction, Deposit, Bill, ManualAdjustment } from "./types";
import { clonePlan, createDefaultPlan } from "./defaultPlan";

function asNumber(value: unknown, field: string): number {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string") {
    const parsed = Number(value);
    if (!Number.isNaN(parsed)) {
      return parsed;
    }
  }
  throw new Error(`${field} must be a number`);
}

function asDay(value: unknown, field: string): number {
  const day = Math.trunc(asNumber(value, field));
  if (day < 1 || day > 30) {
    throw new Error(`${field} must be between 1 and 30`);
  }
  return day;
}

function normalizeActions(value: unknown): PlanAction[] {
  if (!Array.isArray(value)) {
    return Array(30).fill(null);
  }
  const next = value
    .slice(0, 30)
    .map((entry) => (entry === null || entry === undefined ? null : String(entry)));
  while (next.length < 30) {
    next.push(null);
  }
  return next as PlanAction[];
}

function normalizeDeposits(value: unknown): Deposit[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map((entry) => {
    if (typeof entry !== "object" || entry === null) {
      throw new Error("deposit entries must be objects");
    }
    const record = entry as Record<string, unknown>;
    return {
      day: asDay(record.day, "deposit.day"),
      amount: asNumber(record.amount, "deposit.amount"),
    };
  });
}

function normalizeBills(value: unknown): Bill[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map((entry) => {
    if (typeof entry !== "object" || entry === null) {
      throw new Error("bill entries must be objects");
    }
    const record = entry as Record<string, unknown>;
    const name = String(record.name ?? "").trim();
    if (!name) {
      throw new Error("bill.name is required");
    }
    return {
      day: asDay(record.day, "bill.day"),
      name,
      amount: asNumber(record.amount, "bill.amount"),
    };
  });
}

function normalizeManualAdjustments(value: unknown): ManualAdjustment[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map((entry) => {
    if (typeof entry !== "object" || entry === null) {
      throw new Error("manual_adjustments entries must be objects");
    }
    const record = entry as Record<string, unknown>;
    return {
      day: asDay(record.day, "manual_adjustments.day"),
      amount: asNumber(record.amount, "manual_adjustments.amount"),
      note: record.note ? String(record.note) : undefined,
    };
  });
}

export function normalizePlan(raw: unknown): Plan {
  if (typeof raw !== "object" || raw === null) {
    throw new Error("plan payload must be an object");
  }
  const data = raw as Record<string, unknown>;
  const plan: Plan = {
    start_balance: asNumber(data.start_balance, "start_balance"),
    target_end: asNumber(data.target_end, "target_end"),
    band: asNumber(data.band, "band"),
    rent_guard: asNumber(data.rent_guard, "rent_guard"),
    deposits: normalizeDeposits(data.deposits),
    bills: normalizeBills(data.bills),
    actions: normalizeActions(data.actions),
    manual_adjustments: normalizeManualAdjustments(data.manual_adjustments),
    locks: Array.isArray(data.locks)
      ? (data.locks as unknown[])
          .filter((entry): entry is [unknown, unknown] =>
            Array.isArray(entry) && entry.length === 2
          )
          .map(([start, end]) => [asDay(start, "locks[0]"), asDay(end, "locks[1]")])
      : [],
    metadata:
      typeof data.metadata === "object" && data.metadata !== null
        ? Object.entries(data.metadata as Record<string, unknown>)
            .filter(([, value]) => typeof value === "string")
            .reduce<Record<string, string>>((acc, [key, value]) => {
              acc[key] = value as string;
              return acc;
            }, {})
        : {},
  };

  plan.deposits.sort((a, b) => a.day - b.day);
  plan.bills.sort((a, b) => a.day - b.day || a.name.localeCompare(b.name));
  plan.manual_adjustments.sort((a, b) => a.day - b.day);

  return clonePlan(plan);
}

export function planToJson(plan: Plan): string {
  return JSON.stringify(plan, null, 2);
}

export function resetPlanState(): Plan {
  return createDefaultPlan();
}
