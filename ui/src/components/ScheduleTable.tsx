import React, { useState } from 'react'
import type { SolveResultOut } from '../types'

type Props = {
  data?: SolveResultOut
  onSetEod: (day: number, eod: number) => Promise<void>
}

export const ScheduleTable: React.FC<Props> = ({ data, onSetEod }) => {
  const [editing, setEditing] = useState<number | null>(null)
  const [inputVal, setInputVal] = useState('')

  if (!data) return null

  const startEdit = (day: number, current: string) => {
    setEditing(day)
    setInputVal(current)
  }

  const commit = async (day: number) => {
    const n = Number(inputVal)
    if (Number.isFinite(n)) {
      await onSetEod(day, n)
    }
    setEditing(null)
  }

  return (
    <div className="table-wrap">
      <table className="schedule">
        <thead>
          <tr>
            <th>Day</th>
            <th>Opening</th>
            <th>Deposits</th>
            <th>Action</th>
            <th>Net</th>
            <th>Bills</th>
            <th>Closing</th>
          </tr>
        </thead>
        <tbody>
          {data.ledger.map((r) => (
            <tr key={r.day}>
              <td className="num">{r.day}</td>
              <td className="num">{r.opening}</td>
              <td className="num">{r.deposits}</td>
              <td className="act"><span className={`badge ${r.action}`}>{r.action}</span></td>
              <td className="num">{r.net}</td>
              <td className="num">{r.bills}</td>
              <td className="num closing" onClick={() => startEdit(r.day, r.closing)}>
                {editing === r.day ? (
                  <input
                    autoFocus
                    className="money"
                    value={inputVal}
                    onChange={(e) => setInputVal(e.target.value)}
                    onBlur={() => commit(r.day)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') commit(r.day)
                      if (e.key === 'Escape') setEditing(null)
                    }}
                  />
                ) : (
                  r.closing
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

