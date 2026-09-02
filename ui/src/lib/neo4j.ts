import neo4j, { type Driver, isInt } from 'neo4j-driver'

// Neo4j's count() (and any other 64-bit integer field) comes back as a
// neo4j.Integer ({low, high}), not a plain JS number — React throws
// rendering it directly as a child. Safe here: these are small demo counts.
function toNum(v: unknown): number {
  return isInt(v) ? v.toNumber() : Number(v)
}

let driver: Driver | null = null

function getDriver(): Driver {
  if (!driver) {
    const uri = import.meta.env.VITE_NEO4J_URI
    const user = import.meta.env.VITE_NEO4J_USER
    const password = import.meta.env.VITE_NEO4J_PASSWORD
    driver = neo4j.driver(uri, neo4j.auth.basic(user, password))
  }
  return driver
}

async function run<T = Record<string, unknown>>(
  cypher: string,
  params: Record<string, unknown> = {},
): Promise<T[]> {
  const session = getDriver().session()
  try {
    const result = await session.run(cypher, params)
    return result.records.map((r) => r.toObject() as T)
  } finally {
    await session.close()
  }
}

export interface IdentityInventory {
  tenant: { name: string; domain: string } | null
  userCount: number
  groupCount: number
  appCount: number
  grantCount: number
  users: { email: string; department: string; isAdmin: boolean }[]
  apps: { name: string }[]
}

export async function fetchIdentityInventory(): Promise<IdentityInventory> {
  const [tenantRows, countRows, userRows, appRows] = await Promise.all([
    run<{ name: string; domain: string }>(
      'MATCH (t:GoogleWorkspaceTenant) RETURN t.name AS name, t.domain AS domain LIMIT 1',
    ),
    run<{ users: number; groups: number; apps: number; grants: number }>(`
      OPTIONAL MATCH (u:GoogleWorkspaceUser)
      WITH count(u) AS users
      OPTIONAL MATCH (g:GoogleWorkspaceGroup)
      WITH users, count(g) AS groups
      OPTIONAL MATCH (a:GoogleWorkspaceOAuthApp)
      WITH users, groups, count(a) AS apps
      OPTIONAL MATCH ()-[r:AUTHORIZED]->()
      RETURN users, groups, apps, count(r) AS grants
    `),
    run<{ email: string; department: string; isAdmin: boolean }>(`
      MATCH (u:GoogleWorkspaceUser)
      RETURN u.email AS email,
             u.organization_department AS department,
             u.is_admin AS isAdmin
      ORDER BY u.email
      LIMIT 50
    `),
    run<{ name: string }>(
      'MATCH (a:GoogleWorkspaceOAuthApp) RETURN a.display_text AS name ORDER BY name',
    ),
  ])

  const counts = countRows[0] ?? { users: 0, groups: 0, apps: 0, grants: 0 }

  return {
    tenant: tenantRows[0] ?? null,
    userCount: toNum(counts.users),
    groupCount: toNum(counts.groups),
    appCount: toNum(counts.apps),
    grantCount: toNum(counts.grants),
    users: userRows,
    apps: appRows,
  }
}

export interface GitHubInventory {
  orgName: string | null
  repoCount: number
  repos: { name: string; language: string | null }[]
}

export async function fetchGitHubInventory(): Promise<GitHubInventory> {
  const [orgRows, repoRows] = await Promise.all([
    run<{ name: string }>(
      'MATCH (o:GitHubOrganization) RETURN o.username AS name LIMIT 1',
    ),
    run<{ name: string; language: string | null }>(`
      MATCH (r:GitHubRepository)
      RETURN r.name AS name, r.primarylanguage AS language
      ORDER BY r.name
      LIMIT 50
    `),
  ])
  return {
    orgName: orgRows[0]?.name ?? null,
    repoCount: repoRows.length,
    repos: repoRows,
  }
}

export interface ToxicOAuthGrant {
  email: string
  department: string
  app: string
  scopes: string[]
}

// Copied verbatim from synthetic-data/scenarios/scenario_toxic_oauth.py so
// the UI's numbers never drift from the scenario script's — see that
// file's docstring for why this specific shape (broad Drive/admin scope,
// non-admin user) rather than a rewritten equivalent.
const TOXIC_OAUTH_QUERY = `
MATCH (u:GoogleWorkspaceUser)-[r:AUTHORIZED]->(a:GoogleWorkspaceOAuthApp)
WHERE NONE(scope IN r.scopes WHERE scope CONTAINS "readonly" OR scope CONTAINS ".file")
  AND ANY(scope IN r.scopes WHERE
        scope CONTAINS "https://www.googleapis.com/auth/drive"
        OR scope CONTAINS ":admin:"
      )
  AND u.is_admin = false
RETURN u.email AS email,
       u.organization_department AS department,
       a.display_text AS app,
       r.scopes AS scopes
ORDER BY email
`

export async function fetchToxicOAuthGrants(): Promise<ToxicOAuthGrant[]> {
  return run<ToxicOAuthGrant>(TOXIC_OAUTH_QUERY)
}
