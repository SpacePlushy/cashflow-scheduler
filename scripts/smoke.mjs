#!/usr/bin/env node
// v0 smoke tests for API + UI + Verify
// Usage:
//   UI_URL=https://your-ui.vercel.app \
//   API_URL=https://your-api.vercel.app/api \
//   VERIFY_URL=https://your-verify.fly.dev \
//   BYPASS=wpIlZgPkdpr04Paqz1ZPB9gFBNbzpEnp \
//   node scripts/smoke.mjs

const UI_URL = process.env.UI_URL
const API_URL = process.env.API_URL
const VERIFY_URL = process.env.VERIFY_URL
const BYPASS = process.env.BYPASS

if (!UI_URL) {
  console.error('Missing UI_URL env var')
  process.exit(2)
}

const API = (API_URL && API_URL.length) ? API_URL.replace(/\/$/,'') : (UI_URL.replace(/\/$/,'') + '/api')

function headers() {
  const h = { 'content-type': 'application/json' }
  if (BYPASS) h['x-vercel-protection-bypass'] = BYPASS
  return h
}

function withBypass(url) {
  if (!BYPASS) return url
  try {
    const u = new URL(url)
    u.searchParams.set('x-vercel-protection-bypass', BYPASS)
    return u.toString()
  } catch { return url }
}

async function req(url, init) {
  const headers = (init && init.headers) ? { ...init.headers } : {}
  if (BYPASS && !headers['x-vercel-protection-bypass']) headers['x-vercel-protection-bypass'] = BYPASS
  const res = await fetch(withBypass(url), { ...(init||{}), headers })
  const text = await res.text()
  if (!res.ok) {
    throw new Error(`HTTP ${res.status} ${res.statusText} at ${url}: ${text.slice(0,200)}`)
  }
  try { return JSON.parse(text) } catch { return text }
}

;(async () => {
  console.log('1) UI GET', UI_URL)
  await req(UI_URL)
  console.log('   ✓ UI reachable')

  console.log('2) API GET /health', API)
  const h = await req(`${API}/health`, { headers: headers() })
  console.log('   ✓', h)

  console.log('3) API POST /solve')
  const solve = await req(`${API}/solve`, { method: 'POST', headers: headers(), body: '{}' })
  console.log('   ✓ objective', solve.objective, 'final', solve.final_closing)

  console.log('4) API POST /set_eod (day 12 + $1.00)')
  const day12 = solve.ledger.find(r => r.day === 12)
  const base12 = day12 ? parseFloat(day12.closing) : 0
  const newEod = Math.max(0, base12 + 1)
  const set = await req(`${API}/set_eod`, { method: 'POST', headers: headers(), body: JSON.stringify({ day: 12, eod_amount: newEod }) })
  console.log('   ✓ new final', set.final_closing)

  console.log('5) API POST /export (md)')
  const exp = await req(`${API}/export`, { method: 'POST', headers: headers(), body: JSON.stringify({ format: 'md' }) })
  if (!exp.content || !exp.content.includes('Objective:')) throw new Error('export missing content')
  console.log('   ✓ export length', exp.content.length)

  if (VERIFY_URL) {
    console.log('6) VERIFY POST /verify')
    const v = await req(`${VERIFY_URL}/verify`, { method: 'POST', headers: { 'content-type': 'application/json' } })
    console.log('   ✓ verify', v.ok ? 'OK' : v.detail, v.dp_obj, v.cp_obj)
  } else {
    console.log('6) VERIFY skipped (set VERIFY_URL to enable)')
  }

  console.log('\nAll smoke tests passed')
})().catch(err => { console.error('Smoke failed:', err.message); process.exit(1) })
