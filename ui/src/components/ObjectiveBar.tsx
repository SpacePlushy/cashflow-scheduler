import React from 'react'

type Props = { objective?: number[]; final?: string }

export const ObjectiveBar: React.FC<Props> = ({ objective, final }) => {
  if (!objective) return null
  const [work, b2b, absd, large, sp] = objective
  return (
    <footer className="objective">
      <span className="chip">Workdays: {work}</span>
      <span className="chip">B2B: {b2b}</span>
      <span className="chip">|Δ|: {absd}</span>
      <span className="chip">Large: {large}</span>
      <span className="chip">Single: {sp}</span>
      <span className="final">Final: {final}</span>
    </footer>
  )
}

