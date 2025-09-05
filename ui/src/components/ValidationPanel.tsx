import React from 'react'

type Props = { checks?: [string, boolean, string][] }

export const ValidationPanel: React.FC<Props> = ({ checks }) => {
  if (!checks) return null
  return (
    <aside className="panel">
      <h3>Validation</h3>
      <ul className="checks">
        {checks.map(([name, ok, detail], i) => (
          <li key={i} className={ok ? 'ok' : 'bad'}>
            <span className="name">{name}</span>
            <span className="detail">{detail}</span>
          </li>
        ))}
      </ul>
    </aside>
  )
}

