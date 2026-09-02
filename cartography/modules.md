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

## Rerunning the sync

`scripts/reset.sh` does NOT rerun this (costs a live API round trip on
every reset) — GitHub nodes just stay empty in Neo4j after a
`docker compose down -v` until you run `scripts/sync-github.sh` (or
`scripts/demo.sh`, which does reset + this + a readiness check in one go).

Two real gotchas found running this by hand (Phase 6 validation):

- `cartography` takes `--github-config-env-var`, not a bare token — the
  var must hold base64-encoded JSON: `{"organization": [{"name": ...,
  "url": ..., "token": ...}]}`. `scripts/sync-github.sh` builds this from
  `CARTOGRAPHY_GITHUB_TOKEN`/`CARTOGRAPHY_GITHUB_URL` in `.env`.
- The default `cartography` run also tries aws/azure/gcp/etc. AWS skips
  cleanly when unconfigured; Azure raises a fatal `RuntimeError` instead
  and kills the whole sync before it reaches GitHub. Use
  `--selected-modules github` to scope the run.
- `403 Forbidden` on `actions/secrets` and `actions/variables` per repo
  is expected and non-fatal — the PAT is read-only with no admin scope,
  by design (see Phase 1 target above). Cartography logs a warning and
  moves on.
