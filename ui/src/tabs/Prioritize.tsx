import { buildFindings, type Severity } from '../lib/risk'
import type { LabData } from '../types'

const SEVERITY_LABEL: Record<Severity, string> = {
  critical: 'Critical',
  high: 'High',
  medium: 'Medium',
}

export function Prioritize({ data }: { data: LabData }) {
  const findings = buildFindings(data.toxicGrants, data.agents, data.violations)

  if (findings.length === 0) {
    return (
      <div className="tab-panel">
        <p className="empty-state">
          No findings — run the Phase 3/4 generators and scenario scripts to
          seed some.
        </p>
      </div>
    )
  }

  return (
    <div className="tab-panel">
      <p className="tab-intro">
        {findings.length} finding{findings.length === 1 ? '' : 's'}, naive
        severity buckets (not a tuned score) — sorted critical first.
      </p>
      <ul className="finding-list">
        {findings.map((f) => (
          <li key={f.id} className={`finding finding-${f.severity}`}>
            <span className={`severity-badge severity-${f.severity}`}>
              {SEVERITY_LABEL[f.severity]}
            </span>
            <div className="finding-body">
              <div className="finding-title">{f.title}</div>
              <div className="finding-subtitle">{f.subtitle}</div>
              <div className="finding-detail">{f.detail}</div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
