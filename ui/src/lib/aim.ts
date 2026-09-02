const AIM_URL = import.meta.env.VITE_AIM_API_URL as string

let accessToken: string | null = null
let loginPromise: Promise<string> | null = null

// Logs in as the dedicated "ui-viewer" account (role: manager — the
// minimum role that can read /security/violations). Not the real admin
// account; see .env.example for why. Access tokens are short-lived, so a
// 401 triggers exactly one re-login retry rather than caching forever.
async function login(): Promise<string> {
  const res = await fetch(`${AIM_URL}/api/v1/public/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: import.meta.env.VITE_AIM_VIEWER_EMAIL,
      password: import.meta.env.VITE_AIM_VIEWER_PASSWORD,
    }),
  })
  if (!res.ok) throw new Error(`AIM login failed: ${res.status}`)
  const data = await res.json()
  return data.accessToken as string
}

async function getToken(): Promise<string> {
  if (accessToken) return accessToken
  if (!loginPromise) loginPromise = login()
  accessToken = await loginPromise
  return accessToken
}

async function authedFetch(path: string, retried = false): Promise<Response> {
  const token = await getToken()
  const res = await fetch(`${AIM_URL}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (res.status === 401 && !retried) {
    accessToken = null
    loginPromise = null
    return authedFetch(path, true)
  }
  return res
}

export interface Agent {
  id: string
  name: string
  status: string
  trustScore: number
  capabilities: string[]
  metadata?: { department?: string; synthetic?: boolean }
}

export async function fetchAgents(): Promise<Agent[]> {
  const res = await authedFetch('/api/v1/agents')
  if (!res.ok) throw new Error(`fetchAgents failed: ${res.status}`)
  const data = await res.json()
  const raw = data.agents ?? data.data ?? data
  const list = Array.isArray(raw) ? raw : (raw.agents ?? [])
  return list.map(
    (a: {
      id: string
      name: string
      status: string
      trustScore?: number
      trust_score?: number
      capabilities?: string[]
      metadata?: { department?: string; synthetic?: boolean }
    }) => ({
      id: a.id,
      name: a.name,
      status: a.status,
      trustScore: a.trustScore ?? a.trust_score ?? 0,
      capabilities: a.capabilities ?? [],
      metadata: a.metadata,
    }),
  )
}

export interface Violation {
  id: string
  agentId: string
  agentName: string
  attemptedCapability: string
  severity: string
  isBlocked: boolean
  createdAt: string
}

export async function fetchViolations(): Promise<Violation[]> {
  const res = await authedFetch('/api/v1/security/violations')
  if (!res.ok) throw new Error(`fetchViolations failed: ${res.status}`)
  const data = await res.json()
  const list = data.violations ?? []
  return list.map(
    (v: {
      id: string
      agent_id: string
      agent_name: string
      attempted_capability: string
      severity: string
      is_blocked: boolean
      created_at: string
    }) => ({
      id: v.id,
      agentId: v.agent_id,
      agentName: v.agent_name,
      attemptedCapability: v.attempted_capability,
      severity: v.severity,
      isBlocked: v.is_blocked,
      createdAt: v.created_at,
    }),
  )
}
