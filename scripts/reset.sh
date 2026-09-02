#!/usr/bin/env bash
# Tear down and re-seed the whole stack from scratch.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "No .env found. Copy .env.example to .env and fill in secrets first." >&2
  exit 1
fi
set -a; source .env; set +a

echo "==> Stopping and removing containers + volumes"
docker compose down -v

if ! docker image inspect reco-lab/aim-frontend:local >/dev/null 2>&1; then
  echo "==> reco-lab/aim-frontend:local not found — see aim/README-local-build.md" >&2
  echo "    (published ghcr.io image bakes the wrong API port for this setup)" >&2
  exit 1
fi

echo "==> Bringing up fresh stack"
docker compose up -d

echo "==> Waiting for Neo4j to be healthy"
until docker compose ps neo4j --format '{{.Status}}' | grep -q healthy; do
  sleep 2
done

echo "==> Waiting for AIM backend to be healthy"
until docker compose ps aim-backend --format '{{.Status}}' | grep -q healthy; do
  sleep 2
done

echo "==> Bootstrapping AIM admin account (idempotent)"
docker compose run --rm \
  -e DATABASE_URL="postgresql://postgres:${AIM_POSTGRES_PASSWORD}@aim-postgres:5432/identity?sslmode=disable" \
  aim-backend /app/aim-bootstrap --default --admin-password="$AIM_ADMIN_PASSWORD"

echo "==> Logging in as admin and flipping enforcement mode to strict (default is permissive 'monitoring')"
LOGIN_RESPONSE=$(curl -sf -X POST "http://localhost:${AIM_BACKEND_PORT:-8090}/api/v1/public/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${AIM_ADMIN_EMAIL:-admin@opena2a.org}\",\"password\":\"${AIM_ADMIN_PASSWORD}\"}")
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin)['accessToken'])")
curl -sf -X PUT "http://localhost:${AIM_BACKEND_PORT:-8090}/api/v1/admin/enforcement-settings" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" -H "Content-Type: application/json" \
  -d '{"enforcementMode":"strict"}' >/dev/null

# aim-sdk's local credential cache (~/.aim/) lives outside any Docker volume,
# so `docker compose down -v` wipes the server-side org/user/agent records
# but leaves stale local credentials pointing at dead ids. Without this,
# generate_agents.py and the scenario scripts below would fail confusingly
# (or silently reuse now-invalid agent ids) — see aim/README-local-build.md.
echo "==> Resetting local aim-sdk credential cache (~/.aim)"
rm -rf ~/.aim/agents
python3 - "$LOGIN_RESPONSE" "${AIM_BACKEND_PORT:-8090}" <<'PYEOF'
import json, os, stat, sys

resp = json.loads(sys.argv[1])
port = sys.argv[2]
aim_dir = os.path.expanduser("~/.aim")
os.makedirs(aim_dir, exist_ok=True)
creds = {
    "aimUrl": f"http://localhost:{port}",
    "refreshToken": resp["refreshToken"],
    "accessToken": resp["accessToken"],
    "userId": resp["user"]["id"],
    "userEmail": resp["user"]["email"],
    "organizationId": resp["user"]["organizationId"],
    "schemaVersion": "1.0",
    "type": "sdk_oauth",
}
path = os.path.join(aim_dir, "sdk_credentials.json")
with open(path, "w") as f:
    json.dump(creds, f, indent=2)
os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
PYEOF

if [ -d .venv-synth ]; then
  echo "==> Seeding synthetic identity data"
  # shellcheck disable=SC1091
  source .venv-synth/bin/activate
  python synthetic-data/generate_identities.py
  deactivate
else
  echo "==> .venv-synth not found — skipping synthetic identity seed" >&2
  echo "    python3 -m venv .venv-synth && .venv-synth/bin/pip install faker neo4j" >&2
fi

if [ -d .venv-aim-sdk ]; then
  echo "==> Registering synthetic agent fleet"
  # shellcheck disable=SC1091
  source .venv-aim-sdk/bin/activate
  python synthetic-data/generate_agents.py
  echo "==> Running deny scenario (agent attempts an out-of-scope action)"
  python synthetic-data/scenarios/scenario_agent_exfil.py
  deactivate
else
  echo "==> .venv-aim-sdk not found — skipping agent fleet + scenario" >&2
  echo "    python3 -m venv .venv-aim-sdk && .venv-aim-sdk/bin/pip install aim-sdk" >&2
fi

if [ -d .venv-synth ]; then
  echo "==> Running toxic-OAuth-grant detection scenario"
  # shellcheck disable=SC1091
  source .venv-synth/bin/activate
  python synthetic-data/scenarios/scenario_toxic_oauth.py
  deactivate
fi

echo "==> Stack reset."
echo "    AIM dashboard: http://localhost:${AIM_FRONTEND_PORT:-3000}  (login: ${AIM_ADMIN_EMAIL:-admin@opena2a.org})"
echo "    Cartography's GitHub sync is not run here (costs a live API round"
echo "    trip) — see cartography/modules.md to rerun it."
