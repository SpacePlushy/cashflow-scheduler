import React from 'react'
import type { VerifyOut } from '../types'

type Props = {
  data: VerifyOut
  onClose: () => void
}

const LABELS = ['Workdays', 'Back‑to‑Back', '|Δ| to Target', 'Large Days', 'Single Pen']

function fmt(label: string, v: unknown): string | number {
  if (typeof v !== 'number') return String(v ?? '-')
  if (label.includes('Δ')) {
    const sign = v < 0 ? '-' : ''
    const abs = Math.abs(v)
    return `${sign}${(abs / 100).toFixed(2)}`
  }
  return v
}

export const VerifyDialog: React.FC<Props> = ({ data, onClose }) => {
  const dp = Array.isArray(data.dp_obj) ? data.dp_obj : []
  const cp = Array.isArray(data.cp_obj) ? data.cp_obj : []
  const equalAll = dp.length === cp.length && dp.every((v, i) => v === cp[i]) && data.ok
  const firstDiffIdx = dp.findIndex((v, i) => v !== cp[i])
  const summary = equalAll
    ? 'Objectives match (DP = CP‑SAT)'
    : firstDiffIdx >= 0
      ? `First difference: ${LABELS[firstDiffIdx]} (DP ${fmt(LABELS[firstDiffIdx], dp[firstDiffIdx])} vs CP ${fmt(LABELS[firstDiffIdx], cp[firstDiffIdx])})`
      : data.detail || 'Verification result'

  return (
    <div className="modal" onClick={onClose}>
      <div className="dialog" onClick={(e) => e.stopPropagation()}>
        <h3>Verification: DP vs CP‑SAT</h3>
        <div className="verify-status">
          <span className={`chip ${equalAll ? 'ok' : 'bad'}`}>{equalAll ? 'Match: OK' : 'Mismatch'}</span>
          <span className="muted">{summary}</span>
        </div>

        <table className="verify-table">
          <colgroup>
            <col style={{ width: '60%' }} />
            <col style={{ width: '18%' }} />
            <col style={{ width: '18%' }} />
            <col style={{ width: '4%' }} />
          </colgroup>
          <thead>
            <tr>
              <th scope="col">Metric (lex order)</th>
              <th scope="col" className="num">DP</th>
              <th scope="col" className="num">CP‑SAT</th>
              <th scope="col" className="stat"></th>
            </tr>
          </thead>
          <tbody>
            {LABELS.map((name, i) => {
              const vdp = typeof dp[i] === 'undefined' ? '-' : fmt(name, dp[i])
              const vcp = typeof cp[i] === 'undefined' ? '-' : fmt(name, cp[i])
              const eq = dp[i] === cp[i]
              return (
                <tr key={i}>
                  <td className="lbl">{i + 1}. {name}</td>
                  <td className={`num ${eq ? '' : 'diff'}`}>{vdp}</td>
                  <td className={`num ${eq ? '' : 'diff'}`}>{vcp}</td>
                  <td className="stat">{eq ? '✓' : '≠'}</td>
                </tr>
              )
            })}
          </tbody>
        </table>

        <div className="muted" style={{ marginTop: 8 }}>
          Lexicographic order minimizes (1) Workdays → (2) Back‑to‑Back → (3) |Δ| to Target → (4) Large Days → (5) Single Penalty.
        </div>

        <div className="dialog-actions">
          <button className="btn" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  )
}
