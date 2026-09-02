#!/usr/bin/env bash
# Full pre-demo prep: reset everything, resync GitHub data, verify the
# stack is actually ready to show someone. Run this before rehearsing or
# giving the demo — not something to run mid-demo.
set -euo pipefail
cd "$(dirname "$0")/.."

./scripts/reset.sh
./scripts/sync-github.sh

set -a; source .env; set +a

echo
echo "==> Final readiness check"

echo -n "    Neo4j reachable: "
if curl -sf -o /dev/null "http://localhost:7474"; then echo "yes"; else echo "NO — stop here"; exit 1; fi

echo -n "    AIM backend reachable: "
if curl -sf -o /dev/null "http://localhost:${AIM_BACKEND_PORT:-8090}/health"; then echo "yes"; else echo "NO — stop here"; exit 1; fi

echo -n "    UI reachable: "
if curl -sf -o /dev/null "http://localhost:${UI_PORT:-5173}"; then echo "yes"; else echo "NO — stop here"; exit 1; fi

echo
echo "==> Stack is up and seeded. Open the UI and walk docs/demo-script.md:"
echo "    http://localhost:${UI_PORT:-5173}"
