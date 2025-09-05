import React from 'react'

type Props = {
  onSolve: () => void
  onVerify: () => void
  onExport: (fmt: 'md' | 'csv' | 'json') => void
  solving: boolean
  verifying?: boolean
  status?: string
}

export const Toolbar: React.FC<Props> = ({ onSolve, onVerify, onExport, solving, verifying, status }) => {
  return (
    <header className="toolbar">
      <div className="title">Cashflow</div>
      <div className="actions">
        <button className="btn primary" onClick={onSolve} disabled={solving}>
          {solving ? 'Solving…' : 'Solve'}
        </button>
        <button className="btn" onClick={onVerify} disabled={verifying}>
          {verifying ? 'Verifying…' : 'Verify'}
        </button>
        <div className="export">
          <button className="btn" onClick={() => onExport('md')}>Export MD</button>
          <button className="btn" onClick={() => onExport('csv')}>CSV</button>
          <button className="btn" onClick={() => onExport('json')}>JSON</button>
        </div>
      </div>
      <div className="status">{status}</div>
    </header>
  )
}
