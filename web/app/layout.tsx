import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Cashflow Scheduler',
  description: '30-day cashflow planner'
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
