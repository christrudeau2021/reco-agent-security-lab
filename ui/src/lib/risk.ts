import type { Agent, Violation } from './aim'
import type { ToxicOAuthGrant } from './neo4j'

export type Severity = 'critical' | 'high' | 'medium'

export interface Finding {
  id: string
  severity: Severity
  title: string
  subtitle: string
  detail: string
  source: 'oauth-grant' | 'agent-capability' | 'agent-violation'
  remediationHint: string
}

// Mirrors the namespace-prefix table AIM's own SDK uses (see
// sdk/python/aim_sdk/risk_detector.py, documented in the AIM README):
// payment:, admin:, system:, billing:, finance: are critical-risk
// namespaces regardless of the verb. Naive on purpose (CLAUDE.md Phase 5:
// "start naive") — an ordered bucket, not a tuned weighted score.
const CRITICAL_NAMESPACES = ['payment:', 'admin:', 'system:', 'billing:', 'finance:']

function hasCriticalCapability(capabilities: string[]): string | null {
  return (
    capabilities.find((c) => CRITICAL_NAMESPACES.some((ns) => c.startsWith(ns))) ?? null
  )
}

export function buildFindings(
  toxicGrants: ToxicOAuthGrant[],
  agents: Agent[],
  violations: Violation[],
): Finding[] {
  const findings: Finding[] = []

  for (const g of toxicGrants) {
    findings.push({
      id: `oauth-${g.email}-${g.app}`,
      severity: 'critical',
      title: `${g.email} authorized "${g.app}" with broad scope`,
      subtitle: `${g.department} · non-admin user`,
      detail: `Scopes: ${g.scopes.join(', ')}`,
      source: 'oauth-grant',
      remediationHint: `Revoke "${g.app}" access for ${g.email}`,
    })
  }

  for (const a of agents) {
    const criticalCap = hasCriticalCapability(a.capabilities)
    if (criticalCap) {
      findings.push({
        id: `agent-cap-${a.id}`,
        severity: 'critical',
        title: `Agent "${a.name}" holds broad capability "${criticalCap}"`,
        subtitle: `${a.metadata?.department ?? 'unknown department'} · trust ${Math.round(a.trustScore * 100)}%`,
        detail: `All capabilities: ${a.capabilities.join(', ')}`,
        source: 'agent-capability',
        remediationHint: `Revoke "${criticalCap}" from agent "${a.name}"`,
      })
    }
  }

  for (const v of violations.filter((v) => v.isBlocked)) {
    findings.push({
      id: `violation-${v.id}`,
      severity: 'high',
      title: `Agent "${v.agentName}" attempted "${v.attemptedCapability}" — denied`,
      subtitle: new Date(v.createdAt).toLocaleString(),
      detail: `Severity reported by AIM: ${v.severity}`,
      source: 'agent-violation',
      remediationHint: `Review why "${v.agentName}" attempted an out-of-scope action`,
    })
  }

  const order: Record<Severity, number> = { critical: 0, high: 1, medium: 2 }
  return findings.sort((a, b) => order[a.severity] - order[b.severity])
}
