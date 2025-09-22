export type ShiftCode = "O" | "S" | "M" | "L" | "SS";

export interface Deposit {
  day: number;
  amount: number;
}

export interface Bill {
  day: number;
  name: string;
  amount: number;
}

export interface ManualAdjustment {
  day: number;
  amount: number;
  note?: string;
}

export type PlanAction = ShiftCode | null;

export interface Plan {
  start_balance: number;
  target_end: number;
  band: number;
  rent_guard: number;
  deposits: Deposit[];
  bills: Bill[];
  actions: PlanAction[];
  manual_adjustments: ManualAdjustment[];
  locks: Array<[number, number]>;
  metadata: Record<string, string>;
}

export interface LedgerRow {
  day: number;
  opening: string;
  deposits: string;
  action: ShiftCode | string | null;
  net: string;
  bills: string;
  closing: string;
}

export type ValidationCheck = [label: string, ok: boolean, detail: string];

export interface SolveResponse {
  actions: ShiftCode[];
  objective: number[];
  final_closing: string;
  ledger: LedgerRow[];
  checks: ValidationCheck[];
}

export type ExportFormat = "md" | "csv" | "json";
