"use client"
import { useEffect, useState } from 'react'

type SolveResult = {
  actions: string[]
  objective: number[]
  final_closing: string
  ledger: { day:number; opening:string; deposits:string; action:string; net:string; bills:string; closing:string }[]
  checks: [string, boolean, string][]
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE
const VERIFY_BASE = process.env.NEXT_PUBLIC_VERIFY_BASE

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const base = API_BASE ?? (typeof window !== 'undefined' && location.hostname === 'localhost' ? 'http://127.0.0.1:8000' : '/api')
  const url = base + path
  const res = await fetch(url, { headers: { 'content-type':'application/json' }, ...init })
  if (!res.ok) throw new Error(await res.text())
  return res.json() as Promise<T>
}
async function apiVerify() {
  const base = VERIFY_BASE ?? (typeof window !== 'undefined' && location.hostname === 'localhost' ? 'http://127.0.0.1:8000' : undefined)
  if (!base) throw new Error('Verify service not configured')
  const res = await fetch(base + '/verify', { method:'POST', headers: { 'content-type':'application/json' } })
  if (!res.ok) throw new Error(await res.text())
  return res.json() as Promise<{ ok:boolean; dp_obj:number[]; cp_obj:number[]; detail:string }>
}

export default function Home() {
  const [data, setData] = useState<SolveResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState<string|undefined>()
  const [verifyMsg, setVerifyMsg] = useState<string|undefined>()

  const solve = async () => {
    setLoading(true); setErr(undefined)
    try { setData(await api<SolveResult>('/solve', { method:'POST', body: JSON.stringify({}) })) }
    catch(e:any){ setErr(e.message || String(e)) }
    finally{ setLoading(false) }
  }

  useEffect(() => { solve() }, [])

  return (
    <main style={{ padding:20, fontFamily:'system-ui, -apple-system, Segoe UI, Roboto, Inter, sans-serif' }}>
      <h1>Cashflow</h1>
      <div style={{display:'flex', gap:8, alignItems:'center'}}>
        <button onClick={solve} disabled={loading}>{loading? 'Solving…':'Solve'}</button>
        <button onClick={async ()=>{
          setVerifyMsg(undefined); setErr(undefined)
          try { const v = await apiVerify(); setVerifyMsg(v.ok ? 'Verify: OK' : `Verify: ${v.detail}`) }
          catch(e:any){ setErr(e.message || String(e)) }
        }} disabled={!VERIFY_BASE}>
          Verify
        </button>
        <span style={{color:'#777'}}>{API_BASE ? `API ${API_BASE}` : 'API default (/api)'} {VERIFY_BASE ? ` · Verify ${VERIFY_BASE}` : ''}</span>
      </div>
      {verifyMsg && <div style={{color:'#0c6', padding:'6px 0'}}>{verifyMsg}</div>}
      {err && <pre style={{color:'#c00', background:'#fee', padding:8, border:'1px solid #fbb'}}>{err}</pre>}
      {data && (
        <>
          <p>Final: {data.final_closing} — Objective: {JSON.stringify(data.objective)}</p>
          <table style={{borderCollapse:'collapse', width:'100%'}}>
            <thead>
              <tr>
                {['Day','Opening','Deposits','Action','Net','Bills','Closing'].map(h=>
                  <th key={h} style={{textAlign:'right', borderBottom:'1px solid #ddd', padding:'6px 8px'}}>{h}</th>
                )}
              </tr>
            </thead>
            <tbody>
              {data.ledger.map(r=> (
                <tr key={r.day}>
                  <td style={{textAlign:'right', padding:'6px 8px'}}>{r.day}</td>
                  <td style={{textAlign:'right', padding:'6px 8px'}}>{r.opening}</td>
                  <td style={{textAlign:'right', padding:'6px 8px'}}>{r.deposits}</td>
                  <td style={{textAlign:'center', padding:'6px 8px'}}>{r.action}</td>
                  <td style={{textAlign:'right', padding:'6px 8px'}}>{r.net}</td>
                  <td style={{textAlign:'right', padding:'6px 8px'}}>{r.bills}</td>
                  <td style={{textAlign:'right', padding:'6px 8px'}}>{r.closing}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </main>
  )
}
