import type { Agent, Violation } from './lib/aim'
import type { GitHubInventory, IdentityInventory, ToxicOAuthGrant } from './lib/neo4j'

export interface LabData {
  identity: IdentityInventory
  github: GitHubInventory
  agents: Agent[]
  violations: Violation[]
  toxicGrants: ToxicOAuthGrant[]
}
