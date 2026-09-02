import { useState } from 'react'
import { buildFindings } from '../lib/risk'
import type { LabData } from '../types'

interface LoggedAction {
  id: string
  text: string
  at: string
}

export function Remediate({ data }: { data: LabData }) {
  const findings = buildFindings(data.toxicGrants, data.agents, data.violations)
  const [actionLog, setActionLog] = useState<LoggedAction[]>([])

  // Mocked, per CLAUDE.md Phase 5: this does not call AIM or Neo4j to
  // revoke anything. It only appends to a local, in-memory log. The real
  // audit trail below is AIM's own /security/violations feed.
  function mockRevoke(findingId: string, text: string) {
    setActionLog((prev) => [
      { id: `${findingId}-${Date.now()}`, text: `Would revoke: ${text}`, at: new Date().toLocaleString() },
      ...prev,
    ])
  }

  return (
    <div className="tab-panel">
      <section className="panel">
        <h2>Remediation actions</h2>
        <p className="tab-intro">
          Buttons below log an intended action locally — nothing is actually
          revoked. This is a demo lab, not a production remediation tool.
        </p>
        {findings.length === 0 ? (
          <p className="empty-state">No findings to remediate.</p>
        ) : (
          <ul className="finding-list">
            {findings.map((f) => (
              <li key={f.id} className={`finding finding-${f.severity}`}>
                <div className="finding-body">
                  <div className="finding-title">{f.title}</div>
                  <div className="finding-subtitle">{f.subtitle}</div>
                </div>
                <button onClick={() => mockRevoke(f.id, f.remediationHint)}>
                  Revoke
                </button>
              </li>
            ))}
          </ul>
        )}

        {actionLog.length > 0 && (
          <>
            <h3>Action log (this session, not persisted)</h3>
            <ul className="action-log">
              {actionLog.map((a) => (
                <li key={a.id}>
                  <span className="action-time">{a.at}</span> {a.text}
                </li>
              ))}
            </ul>
          </>
        )}
      </section>

      <section className="panel">
        <h2>Audit trail (real, from AIM)</h2>
        {data.violations.length === 0 ? (
          <p className="empty-state">
            No capability violations logged yet — run{' '}
            <code>synthetic-data/scenarios/scenario_agent_exfil.py</code>.
          </p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Agent</th>
                <th>Attempted capability</th>
                <th>Blocked</th>
                <th>Severity</th>
                <th>When</th>
              </tr>
            </thead>
            <tbody>
              {data.violations
                .slice()
                .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
                .map((v) => (
                  <tr key={v.id}>
                    <td>{v.agentName}</td>
                    <td>{v.attemptedCapability}</td>
                    <td>{v.isBlocked ? 'yes' : 'no (monitoring mode)'}</td>
                    <td>{v.severity}</td>
                    <td>{new Date(v.createdAt).toLocaleString()}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  )
}
