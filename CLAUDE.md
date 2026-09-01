# CLAUDE.md — Reco-Analog Agent & SaaS Security Demo Lab

## Purpose

Chris Trudeau is interviewing for a Channel Solutions Architect role at Reco (Reco.ai), an AI Agent / SaaS Security platform. Reco has no public trial, sandbox, or downloadable build — hands-on access is gated behind a sales demo or partner onboarding. This project builds a **conceptual analog** of Reco's architecture using open-source, Apache 2.0-licensed tools, so Chris can develop real, hands-on fluency in the problem space (identity/permission/connectivity graphing, AI agent capability governance, SaaS posture risk) before walking into partner conversations and, eventually, onboarding.

This is a **personal learning and demo lab**, not a commercial product and not a reconstruction of Reco's actual codebase, UI, or trademarks.

## Explicit Non-Goals (read first)

- This is **not** a clone of Reco's product. Do not copy Reco's UI pixel-for-pixel, use Reco's logo/wordmark/brand colors as your own product identity, or name this project anything that could be confused with Reco or imply Reco endorsement. Reference their public brand guidelines only for *understanding*, not for reproduction.
- Do **not** connect this lab to any real production SaaS tenant, real customer data, or real employer systems without a separate, explicit decision at that time. Default to synthetic data for everything.
- This is **not** a production security tool. Do not represent it as audited, hardened, or suitable for protecting a real organization's data.
- Do not scrape, download, or reproduce any of Reco's non-public material (nothing behind their password-gated `readme.reco.ai/reference`, nothing from a future partner/customer portal). Only their public site and public partner-integration docs were used to inform this project's conceptual scope.

## What We're Building

Two upstream open-source projects, wired together with a synthetic-data layer and a unifying UI that mirrors Reco's own stated UX pattern (**Discover → Prioritize → Remediate**):

1. **[Cartography](https://github.com/cartography-cncf/cartography)** (Apache 2.0, CNCF sandbox project) — pulls identities, permissions, and relationships from SaaS/cloud/identity providers into a Neo4j graph. This stands in for **Reco Graph** (the four-dimension identity/permissions/connectivity/activity model).
2. **[OpenA2A Agent Identity Management (AIM)](https://github.com/opena2a-org/agent-identity-management)** (Apache 2.0) — cryptographic agent identity, capability-based authorization, trust scoring, and audit trails for AI agents. This stands in for Reco's **Agent Security** layer.
3. **A synthetic data generator** — since there is no real tenant to point Cartography at, this populates the graph with realistic fake users, groups, SaaS apps, OAuth grants, and a fleet of synthetic AI agents (some well-behaved, some deliberately over-permissioned or policy-violating) so the demo has something worth looking at.
4. **A unifying dashboard UI** — a single app that queries both Neo4j (via Cypher) and the AIM API, and presents them the way Reco presents its own platform: one view for app/identity/agent discovery, one for risk prioritization, one for remediation actions and audit trail.

## Architecture

```
                        ┌─────────────────────────┐
                        │   Unified Dashboard UI   │
                        │  (Discover / Prioritize /│
                        │      Remediate)          │
                        └────────────┬─────────────┘
                                     │
                 ┌───────────────────┼───────────────────┐
                 │                   │                   │
        ┌────────▼────────┐ ┌────────▼────────┐ ┌────────▼────────┐
        │   Cartography    │ │   AIM Backend    │ │  Synthetic Data  │
        │  (Python, reads  │ │  (Go, Postgres,  │ │    Generator     │
        │   into Neo4j)    │ │  Redis, REST API)│ │  (Python/Faker)  │
        └────────┬────────┘ └────────┬────────┘ └────────┬────────┘
                 │                   │                   │
        ┌────────▼────────┐ ┌────────▼────────┐          │
        │      Neo4j       │ │   PostgreSQL     │◄─────────┘
        │  (identity graph)│ │  (agent registry,│
        │                  │ │  audit log)       │
        └──────────────────┘ └──────────────────┘
```

The synthetic data generator writes into **both** systems: identity/app/permission data goes into Neo4j via Cartography's ingestion pattern (or directly via Cypher for data Cartography has no live connector for), and synthetic agents/capability grants/actions go into AIM via its REST API and Python/TypeScript SDKs.

## Tech Stack

- **Neo4j 5 Community** — graph database (via Cartography's own documented Docker Compose entry)
- **Cartography** — `pip install cartography`, Python 3.11+
- **AIM** — self-hosted mode via `docker compose` (Go backend, Postgres, Redis, React dashboard). Use the **minimal stack** (`aim-postgres aim-backend aim-frontend aim-redis`) — skip the optional Elasticsearch/MinIO/NATS/Prometheus/Grafana/Loki services from AIM's full compose file; they add resource weight for no benefit in a personal demo lab.
- **Synthetic data generator** — Python, `Faker`, direct Neo4j driver (`neo4j` package) + AIM Python SDK (`aim-sdk`)
- **Unifying UI** — a small Next.js (or plain React + Vite) app. Query Neo4j directly with the `neo4j` JS driver for graph views; call the AIM REST API for agent/capability/audit views. Keep it a single-page app with three tabs matching the Discover/Prioritize/Remediate motif.
- **Orchestration** — one root `docker-compose.yml` that brings up Neo4j, AIM's minimal stack, and the UI. The synthetic data generator runs as a one-shot script, not a long-running service.

## Repository Structure

```
reco-agent-security-lab/
  CLAUDE.md                    # this file
  README.md                    # public-facing summary (what/why, not for external sharing without review)
  docker-compose.yml           # top-level orchestration
  .env.example                 # documents every required var; .env itself is gitignored
  cartography/
    modules.md                 # which Cartography modules are enabled and why
  aim/
    docker-compose.aim.yml     # AIM's own compose, included via `include:` or copied in
    policies/                  # capability policy YAML files (deny-by-default examples)
  synthetic-data/
    generate_identities.py     # fake users, groups, SaaS apps, OAuth grants -> Neo4j
    generate_agents.py         # fake AI agents with varying risk profiles -> AIM
    scenarios/
      scenario_toxic_oauth.py  # e.g. an OAuth grant with excessive scope on sensitive data
      scenario_agent_exfil.py  # an agent attempting an out-of-scope action, AIM blocks it
  ui/
    (Next.js or Vite app)
  scripts/
    reset.sh                   # tears down and re-seeds everything from scratch
    demo.sh                    # brings the whole stack up and runs the demo scenarios in order
  docs/
    demo-script.md             # the actual talk track for showing this to someone
```

## Safety & Security Guardrails

These apply regardless of where this is deployed.

**Data**
- Synthetic data only. No real employee names, no real company data, no real customer data, ever, in this repo or its running instances.
- If Chris ever wants to point Cartography at a *real* account (e.g., his own personal Google Workspace or GitHub, to see real output), that requires: a dedicated low-privilege, read-only service account created specifically for this — never his primary identity, never anything with write/admin scope, and never a production or employer-owned account.

**Secrets**
- All credentials live in `.env`, which is gitignored from the first commit. `.env.example` documents every key with placeholder values, never real ones.
- No API keys, tokens, or passwords are ever hardcoded in source files, notebooks, or committed configs.
- AIM's own identity files (`~/.opena2a/aim-core/identity.json` etc.) and OAuth tokens stay on local disk / OS keychain only — never synced to cloud storage, screenshots, or version control.

**Network**
- The full stack binds to `localhost`/the homelab's internal network only by default. Nothing is exposed to the public internet unless a specific, later decision is made to do so (see Deployment section) — and if it is, it goes behind authentication and a firewall allow-list of Chris's own IP, not an open port.

**Agent behavior (AIM policies)**
- Capability policies default to **deny**, not allow. Every synthetic agent should have an explicit, minimal capability grant — mirror how Reco's own pitch works ("least-privilege access," "toxic combinations," "deviates from policy").
- Build at least one scenario where an agent *is* blocked doing something it shouldn't (the AIM README's own A/B demo — same agent code, one instance protected, one not — is a good model to adapt). A demo that only shows "everything works" is less convincing than one that shows the guardrail actually catching something.

**Resource limits**
- Cap the synthetic data generator's agent-action loop (e.g., a max iteration count or a `--max-events` flag) so a bug can't spin up an unbounded number of Neo4j writes or AIM API calls and fill a disk or run up a cloud bill.
- Set Docker memory/CPU limits on each service in `docker-compose.yml` so the stack can't consume an entire homelab host.

**IP / representation**
- Nowhere in the UI, README, or any exported screenshot should this be labeled "Reco" or presented as Reco's product. Label it clearly as what it is: an independent, open-source-based demo built to understand the problem space Reco operates in.

## Deployment Recommendation: Homelab vs. AWS

**Default: build and run this in the homelab.** Reasoning:

- This is an iterative learning project — you'll be tearing it down and rebuilding constantly as you adjust scenarios. Docker Compose on local hardware gives instant iteration with zero cloud cost and zero data-egress or IAM complexity to manage.
- Nothing in this stack needs internet-scale resources. Neo4j + AIM's minimal stack + a small UI comfortably fits in 8-16GB RAM, which most homelab boxes already have.
- Keeping it local also directly satisfies the network guardrail above — nothing is exposed by default.

**Only go to AWS if you specifically need to demo this live to someone outside your network** (e.g., showing Todd or a Reco SE a working instance during a call where screen-share isn't practical, or you want a link you can pull up from anywhere). If that need comes up:

- Don't build a persistent multi-service AWS architecture (no RDS, no ECS, no ALB) — that's cost and complexity this project doesn't need.
- Instead: a single EC2 instance (a `t3.large` is comfortably enough — roughly 8GB RAM) running the exact same `docker-compose.yml`, reached over an SSH tunnel or a WireGuard/Tailscale connection rather than a public port. Spin it up before a demo, tear it down after.
- Put an AWS Budgets alert on the account at a low threshold (e.g., $20) so an accidentally-left-running instance can't surprise you. Left running 24/7 a `t3.large` runs roughly $60-70/month; run only on-demand and it's a few dollars per demo session.
- Use a dedicated IAM user/role scoped to only what this project needs (EC2 start/stop, nothing account-wide), not your root or admin credentials.
- Store the instance as ephemeral — treat local disk as scratch, keep the actual source of truth (this repo, the synthetic data generators, the docker-compose files) in git, so the EC2 instance itself is fully disposable and rebuildable from scratch at any time.

## Build Phases

Work through these in order. Each phase should be independently demoable before moving to the next — don't let scope creep push you to build everything before testing anything.

**Phase 0 — Scaffolding**
Set up the repo structure above, `.env.example`, `docker-compose.yml` skeleton, and `scripts/reset.sh`. Confirm Docker and Docker Compose work in the target environment (homelab first).

**Phase 1 — Cartography standalone**
Get Cartography running against Neo4j with **one real, low-risk data source** to validate the pattern end to end — GitHub is a good first choice (a personal GitHub account, read-only token, public repo data only). Confirm you can run the sample Cypher queries from Cartography's own docs and get real results. This validates the pipeline before synthetic data enters the picture.

**Phase 2 — AIM standalone**
Bring up AIM's minimal self-hosted stack via its own `quickstart.sh` or Docker Compose. Run the Python SDK quickstart (`secure()` + `@perform_action`) against a trivial local script. Confirm the dashboard at `localhost:3000` shows the agent, and that a capability violation actually gets denied — this is the single most important thing to prove works before building anything on top of it.

**Phase 3 — Synthetic data generator (identity side)**
Write `generate_identities.py`: fake users, groups, a set of fake "SaaS apps" with OAuth-style scopes, some deliberately over-permissioned (e.g., a fake app with `admin` scope on a fake "Finance" data source) to give the graph something worth finding. Write directly into Neo4j in Cartography's schema conventions so it's queryable the same way real Cartography data would be.

**Phase 4 — Synthetic data generator (agent side)**
Write `generate_agents.py` and the scenario scripts: a small fleet of synthetic agents registered in AIM with varying capability grants, and at least one scripted scenario where an agent attempts something outside its grant and gets denied, logged, and visible in the audit trail.

**Phase 5 — Unifying UI**
Build the three-tab dashboard (Discover / Prioritize / Remediate) pulling from both systems. Discover = inventory of apps, identities, and agents. Prioritize = a simple risk score (start naive — e.g., flag anything with `admin`/`*` scope, or any agent with a recent denied action) sorted by severity. Remediate = a mocked action button (doesn't need to actually revoke anything for the demo — logging "would revoke X" is fine) plus the real AIM audit log feed.

**Phase 6 — Guardrails pass**
Go back through the Safety & Security Guardrails section above and verify each one against what was actually built — resource limits set, secrets gitignored, deny-by-default policies in place, nothing bound to a public interface. Treat this as a checklist, not a suggestion.

**Phase 7 — Demo script**
Write `docs/demo-script.md`: a 5-10 minute talk track — what you show first, what question each screen answers, and the one moment (the blocked-agent scenario) that's the emotional center of the demo. This is what you'll actually rehearse.

**Phase 8 (optional) — AWS deploy**
Only if the need described above materializes. Reuse the same Docker Compose; don't re-architect for cloud.

## Success Criteria

The lab is "done enough" when you can, without touching a keyboard mid-demo:
1. Show a graph view answering "which identities/agents have access to what" — the same question Cartography's own README leads with.
2. Show a prioritized list of risky findings, not just a raw dump.
3. Show one agent doing something it's allowed to do, and one agent being denied doing something it isn't — live, not screenshotted.
4. Show an audit trail that would satisfy "prove you know what your agents are doing."
5. Explain, in your own words, what's real here (Cartography and AIM are real, running software) versus what's illustrative (the synthetic data, the unified UI, the risk-scoring logic).

## Notes for Claude (working in this repo)

- Default to the homelab deployment path unless told otherwise.
- Never commit anything under `.env`, `*.key`, `*.pem`, or any file matching common credential patterns — check `.gitignore` covers these before the first commit.
- When generating synthetic data, make it clearly synthetic (obviously fake names/domains like `@demo-corp.test`) so there's no risk of it being mistaken for real data later.
- If asked to add a feature that would involve connecting to a real production system, a real employer's SaaS tenant, or storing real personal data, stop and confirm explicitly before proceeding — that's a guardrail, not a formality.
- Keep the UI's own branding generic (e.g., "Ecosystem Security Lab" or similar) — never reuse Reco's name, logo, or exact color palette as this project's own identity.
