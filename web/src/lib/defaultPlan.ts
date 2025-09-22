import { Plan } from "./types";

const basePlan: Plan = {
  start_balance: 90.5,
  target_end: 490.5,
  band: 25,
  rent_guard: 1636,
  deposits: [
    { day: 11, amount: 1021 },
    { day: 25, amount: 1021 },
  ],
  bills: [
    { day: 1, name: "Auto Insurance", amount: 177 },
    { day: 2, name: "YouTube Premium", amount: 8 },
    { day: 5, name: "Groceries", amount: 112.5 },
    { day: 5, name: "Weed", amount: 20 },
    { day: 8, name: "Paramount Plus", amount: 12 },
    { day: 8, name: "iPad AppleCare", amount: 8.49 },
    { day: 10, name: "Streaming Svcs", amount: 230 },
    { day: 11, name: "Cat Food", amount: 40 },
    { day: 12, name: "Groceries", amount: 112.5 },
    { day: 12, name: "Weed", amount: 20 },
    { day: 14, name: "iPad AppleCare", amount: 8.49 },
    { day: 16, name: "Cat Food", amount: 40 },
    { day: 17, name: "Car Payment", amount: 463 },
    { day: 19, name: "Groceries", amount: 112.5 },
    { day: 19, name: "Weed", amount: 20 },
    { day: 22, name: "Cell Phone", amount: 177 },
    { day: 23, name: "Cat Food", amount: 40 },
    { day: 24, name: "AI Subscription", amount: 220 },
    { day: 25, name: "Electric", amount: 139 },
    { day: 25, name: "Ring Subscription", amount: 10 },
    { day: 26, name: "Groceries", amount: 112.5 },
    { day: 26, name: "Weed", amount: 20 },
    { day: 28, name: "iPhone AppleCare", amount: 13.49 },
    { day: 29, name: "Internet", amount: 30 },
    { day: 29, name: "Cat Food", amount: 40 },
    { day: 30, name: "Rent", amount: 1636 },
  ],
  actions: Array(30).fill(null),
  manual_adjustments: [],
  locks: [],
  metadata: { version: "1.0.0", source: "ui" },
};

export const defaultPlan = clonePlan(basePlan);

export const defaultPlanJson = JSON.stringify(basePlan, null, 2);

export function clonePlan(plan: Plan): Plan {
  return {
    ...plan,
    deposits: plan.deposits.map((d) => ({ ...d })),
    bills: plan.bills.map((b) => ({ ...b })),
    actions: [...plan.actions],
    manual_adjustments: plan.manual_adjustments.map((a) => ({ ...a })),
    locks: plan.locks.map((lock) => [...lock] as [number, number]),
    metadata: { ...plan.metadata },
  };
}

export function createDefaultPlan(): Plan {
  return clonePlan(basePlan);
}
