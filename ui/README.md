# Ecosystem Security Lab — UI

The Discover / Prioritize / Remediate dashboard. React + TypeScript + Vite, no backend of its own — it queries Neo4j directly over bolt-over-websocket and calls AIM's REST API as a dedicated least-privilege service account (see `.env.example` for why, and the root `README.md` for the full picture).

## Local dev

```bash
npm install
npm run dev       # http://localhost:5173, expects the rest of the stack already up
```

## Container build

Built and run as part of the root `docker-compose.yml`; see `Dockerfile` in this directory. `VITE_*` env vars are baked in at build time (Vite inlines them into the client bundle), so they're passed as Docker build args, not left to `environment:` at runtime.

## Structure

- `src/lib/neo4j.ts` — identity/GitHub graph queries
- `src/lib/aim.ts` — AIM API client (auth, agents, violations)
- `src/lib/risk.ts` — naive severity scoring that turns raw data into `Finding[]`
- `src/tabs/` — the three tabs
