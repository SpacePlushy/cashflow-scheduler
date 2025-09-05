import React, { useEffect, useState } from 'react'
import { api } from './api'
import type { SolveResultOut, ExportOut, VerifyOut } from './types'
import { Toolbar } from './components/Toolbar'
import { ScheduleTable } from './components/ScheduleTable'
import { ValidationPanel } from './components/ValidationPanel'
import { ObjectiveBar } from './components/ObjectiveBar'
import { VerifyDialog } from './components/VerifyDialog'

const App: React.FC = () => {
  const [health, setHealth] = useState<string>('')
  const [solving, setSolving] = useState(false)
  const [data, setData] = useState<SolveResultOut | undefined>()
  const [exportText, setExportText] = useState<ExportOut | null>(null)
  const [verifying, setVerifying] = useState(false)
  const [verifyData, setVerifyData] = useState<VerifyOut | null>(null)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    api.health().then((h) => setHealth(`${h.status} · v${h.version}`)).catch(() => setHealth('offline'))
    doSolve()
  }, [])

  const doSolve = async () => {
    setSolving(true)
    setErr(null)
    try {
      const res = await api.solve()
      setData(res)
    } catch (e: any) {
      setErr(e.message || String(e))
    } finally {
      setSolving(false)
    }
  }

  const onSetEod = async (day: number, amount: number) => {
    setSolving(true)
    setErr(null)
    try {
      const res = await api.setEod(day, amount)
      setData(res)
    } catch (e: any) {
      setErr(e.message || String(e))
    } finally {
      setSolving(false)
    }
  }

  const onExport = async (fmt: 'md' | 'csv' | 'json') => {
    try {
      const out = await api.export(fmt)
      setExportText(out)
    } catch (e: any) {
      setErr(e.message || String(e))
    }
  }

  const onVerify = async () => {
    setVerifying(true)
    setErr(null)
    try {
      const v = await api.verify()
      setVerifyData(v)
    } catch (e: any) {
      setErr(e.message || String(e))
    } finally {
      setVerifying(false)
    }
  }

  return (
    <div className="app">
      <Toolbar onSolve={doSolve} onVerify={onVerify} onExport={onExport} solving={solving} verifying={verifying} status={health} />
      {err && <div className="banner error">{err}</div>}
      <main className="content">
        <div className="left">
          <ScheduleTable data={data} onSetEod={onSetEod} />
        </div>
        <div className="right">
          <ValidationPanel checks={data?.checks} />
        </div>
      </main>
      <ObjectiveBar objective={data?.objective} final={data?.final_closing} />

      {exportText && (
        <div className="modal" onClick={() => setExportText(null)}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <h3>Export ({exportText.format})</h3>
            <textarea readOnly value={exportText.content} />
            <div className="dialog-actions">
              <button className="btn" onClick={() => setExportText(null)}>Close</button>
            </div>
          </div>
        </div>
      )}

      {verifyData && (
        <VerifyDialog data={verifyData} onClose={() => setVerifyData(null)} />
      )}
    </div>
  )
}

export default App
