# Cartography modules enabled

Phase 1 target: GitHub module only, read-only fine-grained PAT (Public
repositories: read-only, no account permissions), scoped to
`christrudeau2021`.

Cartography's github module queries `organization(login: ...)` in the
GitHub GraphQL API — it is org-scoped, not user-scoped, so it cannot target
a personal account's own repos directly. Phase 1 instead points it at
**opena2a-org** (the public org behind the AIM project this lab is built
on) to validate the ingestion pattern against real, public data with zero
blast radius.

Phase 1 validated 2026-09-01: synced against local Neo4j with no errors.
Result: 1 GitHubOrganization, 23 GitHubRepository, 482 GitHubDependency,
68 GitHubWorkflow, 35 GitHubAction, 23 GitHubBranch nodes. Sample Cypher
queries from Cartography's own docs (org lookup, repo listing, node counts
by label) all returned real results.

| Module | Enabled | Why |
|---|---|---|
| github | yes (Phase 1) | Low-risk real data source to validate ingestion pattern end-to-end |
| others | not yet | Added if a scenario needs them; synthetic data covers the rest directly via Cypher |
