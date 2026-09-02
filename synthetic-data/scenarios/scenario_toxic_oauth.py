#!/usr/bin/env python3
"""
Scenario: detect the toxic OAuth grant planted by generate_identities.py.

This is the read side of the identity-graph toxic-combination example —
generate_identities.py writes the grant, this script finds it the way a
Prioritize view (Phase 5) would: broad/admin-shaped OAuth scopes held by a
user with no admin role and no obvious job-function reason to have them.

Requires: generate_identities.py already run against this Neo4j instance.
"""

import os
import sys

from neo4j import GraphDatabase

# Scopes that read as "broad" regardless of which app grants them — full
# Drive read/write, or anything with an admin-shaped custom scope string.
RISKY_SCOPE_MARKERS = ["https://www.googleapis.com/auth/drive", ":admin:"]

QUERY = """
MATCH (u:GoogleWorkspaceUser)-[r:AUTHORIZED]->(a:GoogleWorkspaceOAuthApp)
WHERE NONE(scope IN r.scopes WHERE scope CONTAINS "readonly" OR scope CONTAINS ".file")
  AND ANY(scope IN r.scopes WHERE
        scope CONTAINS "https://www.googleapis.com/auth/drive"
        OR scope CONTAINS ":admin:"
      )
  AND u.is_admin = false
RETURN u.email AS email,
       u.organization_department AS department,
       a.display_text AS app,
       r.scopes AS scopes
ORDER BY email
"""


def main() -> int:
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD")
    if not password:
        print("NEO4J_PASSWORD not set.", file=sys.stderr)
        return 1

    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            rows = list(session.run(QUERY))
    finally:
        driver.close()

    if not rows:
        print("No toxic OAuth grants found. Run generate_identities.py first.")
        return 1

    print(f"Found {len(rows)} toxic OAuth grant(s) — broad scope, non-admin user:\n")
    for row in rows:
        print(f"  {row['email']} ({row['department']})")
        print(f"    -> authorized '{row['app']}' with scopes: {row['scopes']}")
        print(
            "    Risk: full Drive access and/or admin-shaped scope granted to a "
            "user with no admin role and no stated reason tied to their department."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
