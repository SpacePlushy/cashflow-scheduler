export type PlanIn = {
  start_balance: number
  target_end: number
  band: number
  rent_guard: number
  deposits: { day: number; amount: number }[]
  bills: { day: number; name: string; amount: number }[]
  actions: (string | null)[]
  manual_adjustments: { day: number; amount: number; note?: string }[]
  metadata?: Record<string, string>
}

export type LedgerRowOut = {
  day: number
  opening: string
  deposits: string
  action: string
  net: string
  bills: string
  closing: string
}

export type SolveResultOut = {
  actions: string[]
  objective: number[]
  final_closing: string
  ledger: LedgerRowOut[]
  checks: [string, boolean, string][]
}

export type ExportOut = {
  format: 'md' | 'csv' | 'json'
  content: string
}

export type VerifyOut = {
  ok: boolean
  dp_obj: number[]
  cp_obj: number[]
  detail: string
}

export type HealthOut = { status: string; version: string }

