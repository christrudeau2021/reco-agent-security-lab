#!/usr/bin/env bash
# Re-run Cartography's GitHub sync against the running Neo4j.
#
# reset.sh does NOT do this automatically — every `docker compose down -v`
# wipes Neo4j's data volume, and re-syncing costs a live GitHub API round
# trip, so it's a separate, explicit step. Run this after reset.sh (or any
# time you want fresh repo data) and before a demo.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "No .env found. Copy .env.example to .env and fill in secrets first." >&2
  exit 1
fi
set -a; source .env; set +a

if [ ! -d .venv-cartography ]; then
  echo "==> .venv-cartography not found — skipping GitHub sync" >&2
  echo "    python3 -m venv .venv-cartography && .venv-cartography/bin/pip install cartography" >&2
  exit 1
fi

# Cartography's github module wants a base64-encoded JSON config, not a
# bare token — see cartography/modules.md for the org-scoped (not
# user-scoped) reasoning behind targeting opena2a-org.
export CARTOGRAPHY_GITHUB_CONFIG
CARTOGRAPHY_GITHUB_CONFIG=$(python3 -c "
import json, base64, os
cfg = {'organization': [{'name': 'opena2a-org', 'url': os.environ['CARTOGRAPHY_GITHUB_URL'], 'token': os.environ['CARTOGRAPHY_GITHUB_TOKEN']}]}
print(base64.b64encode(json.dumps(cfg).encode()).decode())
")
export NEO4J_PASSWORD="${NEO4J_AUTH#neo4j/}"

echo "==> Running Cartography GitHub sync (opena2a-org) — this hits the live GitHub API"
# shellcheck disable=SC1091
source .venv-cartography/bin/activate
# --selected-modules github: the default run also tries aws/azure/gcp/etc,
# and Azure raises fatally (not a soft skip) when unconfigured — see
# cartography/modules.md. 403s on actions/secrets and actions/variables
# below are expected: the PAT is read-only, no admin scope, by design.
cartography --neo4j-uri "${NEO4J_URI:-bolt://localhost:7687}" \
  --neo4j-user neo4j --neo4j-password-env-var NEO4J_PASSWORD \
  --github-config-env-var CARTOGRAPHY_GITHUB_CONFIG \
  --selected-modules github
deactivate

echo "==> GitHub sync complete."
