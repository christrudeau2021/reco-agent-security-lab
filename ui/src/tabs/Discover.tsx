import type { LabData } from '../types'

function EmptyState({ children }: { children: React.ReactNode }) {
  return <p className="empty-state">{children}</p>
}

export function Discover({ data }: { data: LabData }) {
  const { identity, github, agents } = data

  return (
    <div className="tab-panel">
      <section className="panel">
        <h2>Identities &amp; SaaS apps</h2>
        {identity.tenant ? (
          <>
            <div className="stat-row">
              <Stat label="Tenant" value={identity.tenant.domain} />
              <Stat label="Users" value={identity.userCount} />
              <Stat label="Groups" value={identity.groupCount} />
              <Stat label="OAuth apps" value={identity.appCount} />
              <Stat label="Grants" value={identity.grantCount} />
            </div>
            <details>
              <summary>{identity.users.length} users (showing up to 50)</summary>
              <table>
                <thead>
                  <tr>
                    <th>Email</th>
                    <th>Department</th>
                    <th>Admin</th>
                  </tr>
                </thead>
                <tbody>
                  {identity.users.map((u) => (
                    <tr key={u.email}>
                      <td>{u.email}</td>
                      <td>{u.department}</td>
                      <td>{u.isAdmin ? 'yes' : ''}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </details>
          </>
        ) : (
          <EmptyState>
            No identity data — run <code>synthetic-data/generate_identities.py</code>.
          </EmptyState>
        )}
      </section>

      <section className="panel">
        <h2>AI agents</h2>
        {agents.length > 0 ? (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Status</th>
                <th>Trust</th>
                <th>Capabilities</th>
              </tr>
            </thead>
            <tbody>
              {agents.map((a) => (
                <tr key={a.id}>
                  <td>{a.name}</td>
                  <td>{a.status}</td>
                  <td>{Math.round(a.trustScore * 100)}%</td>
                  <td>{a.capabilities.join(', ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <EmptyState>
            No agents registered — run <code>synthetic-data/generate_agents.py</code>.
          </EmptyState>
        )}
      </section>

      <section className="panel">
        <h2>Code &amp; repositories</h2>
        {github.repoCount > 0 ? (
          <>
            <div className="stat-row">
              <Stat label="Org" value={github.orgName ?? '—'} />
              <Stat label="Repos" value={github.repoCount} />
            </div>
            <table>
              <thead>
                <tr>
                  <th>Repository</th>
                  <th>Language</th>
                </tr>
              </thead>
              <tbody>
                {github.repos.map((r) => (
                  <tr key={r.name}>
                    <td>{r.name}</td>
                    <td>{r.language ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        ) : (
          <EmptyState>
            No GitHub data — this is expected after a fresh reset (Cartography's
            GitHub sync isn't re-run automatically; see{' '}
            <code>cartography/modules.md</code>).
          </EmptyState>
        )}
      </section>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="stat">
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  )
}
