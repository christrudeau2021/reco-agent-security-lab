#!/usr/bin/env bash
# Tear down and re-seed the whole stack from scratch.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Stopping and removing containers + volumes"
docker compose down -v

echo "==> Bringing up fresh stack"
docker compose up -d

echo "==> Waiting for Neo4j to be healthy"
until docker compose ps neo4j | grep -q "healthy"; do
  sleep 2
done

echo "==> Stack reset. Run synthetic-data generators next (Phase 3+)."
