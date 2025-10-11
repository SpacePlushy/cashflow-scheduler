export interface Plan {
  start_balance: number;
  target_end: number;
  band: number;
  rent_guard: number;
  deposits: Deposit[];
  bills: Bill[];
  actions: (string | null)[];
  manual_adjustments: Adjustment[];
  locks: [number, number][];
  metadata: { version: string };
}

export interface Deposit {
  day: number;
  amount: number;
}

export interface Bill {
  day: number;
  name: string;
  amount: number;
}

export interface Adjustment {
  day: number;
  amount: number;
  note?: string;
}

export interface LedgerRow {
  day: number;
  opening: string;
  deposits: string;
  action: string;
  net: string;
  bills: string;
  closing: string;
}

export interface ValidationCheck {
  name: string;
  ok: boolean;
  detail: string;
}

// API returns checks as tuples [name, ok, detail]
export type ValidationCheckTuple = [string, boolean, string];

export interface Schedule {
  actions: string[];
  objective: number[];
  final_closing: string;
  ledger: LedgerRow[];
  checks: ValidationCheckTuple[];
  solver?: {
    name: string;
    statuses: string[];
    seconds: number;
    fallback_reason?: string;
  };
}
