# Ecosystem Security Lab

Personal learning lab combining two open-source projects to explore AI agent / SaaS security concepts hands-on:

- **[Cartography](https://github.com/cartography-cncf/cartography)** — identity/permission/connectivity graph in Neo4j.
- **[OpenA2A Agent Identity Management (AIM)](https://github.com/opena2a-org/agent-identity-management)** — cryptographic agent identity, capability-based authorization, audit trails.

Plus a synthetic-data generator and a small unifying dashboard (Discover / Prioritize / Remediate).

This is an independent, open-source-based demo built to understand a problem space — not a clone or reproduction of any commercial product. See `CLAUDE.md` for full scope, guardrails, and build phases.

## Status

Phase 0 — scaffolding. Not yet runnable end-to-end.

## Quickstart (once later phases land)

```bash
cp .env.example .env   # fill in real values, never commit .env
docker compose up -d
./scripts/reset.sh      # tear down + re-seed from scratch
```

Deploys to the homelab by default (see `CLAUDE.md`, Deployment Recommendation).
