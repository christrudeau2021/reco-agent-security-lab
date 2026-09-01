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

echo "==> Flipping AIM enforcement mode to strict (default is permissive 'monitoring')"
ACCESS_TOKEN=$(curl -sf -X POST "http://localhost:${AIM_BACKEND_PORT:-8090}/api/v1/public/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${AIM_ADMIN_EMAIL:-admin@opena2a.org}\",\"password\":\"${AIM_ADMIN_PASSWORD}\"}" \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['accessToken'])")
curl -sf -X PUT "http://localhost:${AIM_BACKEND_PORT:-8090}/api/v1/admin/enforcement-settings" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" -H "Content-Type: application/json" \
  -d '{"enforcementMode":"strict"}' >/dev/null

echo "==> Stack reset."
echo "    AIM dashboard: http://localhost:${AIM_FRONTEND_PORT:-3000}  (login: ${AIM_ADMIN_EMAIL:-admin@opena2a.org})"
echo "    Newly-registered agents still need 'Verify agent' clicked in the"
echo "    dashboard before strict mode differentiates their capabilities —"
echo "    see aim/README-local-build.md."
echo "    Run synthetic-data generators next (Phase 3+)."
