import { NextRequest } from 'next/server'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || ''
const API_BYPASS = process.env.API_BYPASS_SECRET || process.env.VERCEL_AUTOMATION_BYPASS_SECRET || ''

async function forward(req: NextRequest, segments: string[]) {
  if (!API_BASE) {
    return new Response('API base not configured', { status: 500 })
  }
  const base = API_BASE.replace(/\/$/, '')
  // Route through the FastAPI index function to avoid stale single-file handlers
  const url = new URL(`${base}/index/${segments.join('/')}`)
  if (API_BYPASS) url.searchParams.set('x-vercel-protection-bypass', API_BYPASS)

  const init: RequestInit = {
    method: req.method,
    headers: {
      'content-type': req.headers.get('content-type') || 'application/json',
      'x-forwarded-host': req.headers.get('host') || '',
    },
  }
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    init.body = await req.text()
  }
  const res = await fetch(url.toString(), init)
  const body = await res.text()
  return new Response(body, {
    status: res.status,
    headers: {
      'content-type': res.headers.get('content-type') || 'application/json',
    },
  })
}

export async function GET(req: NextRequest, { params }: { params: { path: string[] } }) {
  return forward(req, params.path)
}
export async function POST(req: NextRequest, { params }: { params: { path: string[] } }) {
  return forward(req, params.path)
}
export async function OPTIONS(req: NextRequest, { params }: { params: { path: string[] } }) {
  // Preflight passthrough
  return forward(req, params.path)
}
