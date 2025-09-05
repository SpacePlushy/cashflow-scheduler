import type { PlanIn, SolveResultOut, ExportOut, VerifyOut, HealthOut } from './types'

// API base: use Vite env if provided; otherwise for localhost default to FastAPI dev port; in production use same-origin (/api)
const ENV_BASE = (import.meta as any).env?.VITE_API_BASE as string | undefined
const API = ENV_BASE ?? (typeof window !== 'undefined' && window.location.hostname === 'localhost' ? 'http://127.0.0.1:8000' : '')

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(API + path, {
    headers: { 'content-type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const txt = await res.text()
    throw new Error(`${res.status} ${res.statusText}: ${txt}`)
  }
  return (await res.json()) as T
}

export const api = {
  health: () => req<HealthOut>('/api/health'),
  getPlan: () => req<PlanIn>('/api/plan'),
  setPlan: (plan: PlanIn, write = false) =>
    req<PlanIn>('/api/plan', { method: 'POST', body: JSON.stringify({ plan, write }) }),
  solve: (plan?: PlanIn) =>
    req<SolveResultOut>('/api/solve', { method: 'POST', body: JSON.stringify({ plan }) }),
  setEod: (day: number, eod_amount: number) =>
    req<SolveResultOut>('/api/set-eod', { method: 'POST', body: JSON.stringify({ day, eod_amount }) }),
  export: (format: 'md' | 'csv' | 'json') =>
    req<ExportOut>('/api/export', { method: 'POST', body: JSON.stringify({ format }) }),
  verify: () => req<VerifyOut>('/api/verify'),
}
