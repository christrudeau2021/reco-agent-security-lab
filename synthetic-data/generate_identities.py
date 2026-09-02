#!/usr/bin/env python3
"""
Synthetic identity data generator (Phase 3).

Writes fake users, groups, and SaaS OAuth-app grants directly into Neo4j
using Cartography's own Google Workspace schema conventions (labels,
property names, relationship types/directions) — see
cartography/models/googleworkspace/{tenant,user,group,oauth_app}.py in a
local Cartography checkout — so the data is queryable exactly the way real
Cartography output would be. This is a generator, not a Cartography module:
no real Google Workspace account is involved.

Schema written (verified against this repo's own Phase-1 Cartography output:
GitHubOrganization-[:RESOURCE]->GitHubRepository etc. — RESOURCE always
points container -> contained):
  (:GoogleWorkspaceTenant {id, domain, name})
    -[:RESOURCE]->(:GoogleWorkspaceUser {id, primary_email, email, name, is_admin, ...})
    -[:RESOURCE]->(:GoogleWorkspaceGroup {id, name, email})
    -[:RESOURCE]->(:GoogleWorkspaceOAuthApp:ThirdPartyApp {client_id, display_text, ...})
  (:GoogleWorkspaceUser)-[:MEMBER_OF]->(:GoogleWorkspaceGroup)
  (:GoogleWorkspaceUser)-[:AUTHORIZED {scopes}]->(:GoogleWorkspaceOAuthApp)

One app is deliberately over-permissioned (full Drive read/write plus a
custom "finance:admin" scope) and granted to a fixed, non-finance,
non-admin fixture user ("Priya Shah", Marketing) — a toxic-combination
example for the Prioritize view to flag later. Pinned rather than randomly
rolled so the demo talk track (Phase 7) can name the same person every run.

Every node is MERGEd on a standalone line and bound to a variable before
any relationship MERGE — an inline `(:Label {id: ...})` inside a
relationship-MERGE pattern is part of the pattern Cypher tries to match as a
whole, so if the specific relationship doesn't exist yet it creates a new
node too, even when a node with that id already exists elsewhere. (First
version of this script had that bug: reran into 217 tenant nodes from 200
users each creating their own MERGEd copy of "the" tenant.) Uniqueness
constraints on id are the tripwire: if this regresses, Neo4j raises a
constraint violation instead of silently duplicating nodes.

Idempotent: rerunning with the same --seed/--domain/--max-users produces
identical node and relationship counts — every write is a MERGE keyed on a
stable id, never a CREATE. Capped by --max-users (SYNTH_MAX_USERS in .env)
so a bad run can't fill the database.
"""

import argparse
import os
import sys
import uuid

from faker import Faker
from neo4j import GraphDatabase

GROUPS = ["Engineering", "Sales", "Finance", "IT-Admins", "Marketing"]

# (app display name, scopes, over_permissioned)
APPS = [
    ("Slack", ["https://www.googleapis.com/auth/userinfo.email"], False),
    ("Zoom", ["https://www.googleapis.com/auth/calendar.readonly"], False),
    ("Notion", ["https://www.googleapis.com/auth/drive.readonly"], False),
    ("GitHub Desktop Sync", ["https://www.googleapis.com/auth/userinfo.email"], False),
    (
        "Salesforce Data Exporter",
        ["https://www.googleapis.com/auth/drive.readonly"],
        False,
    ),
    (
        "Standup Scheduling Bot",
        ["https://www.googleapis.com/auth/calendar.events"],
        False,
    ),
    ("QuickBooks Connector", ["https://www.googleapis.com/auth/drive.file"], False),
    (
        # Deliberately over-permissioned: full Drive read/write plus a
        # custom admin-scoped grant on a fake sensitive data source, matching
        # CLAUDE.md's "toxic combination" example.
        "FinanceReports AI Agent",
        ["https://www.googleapis.com/auth/drive", "finance:admin:full_access"],
        True,
    ),
]

TOXIC_APP_NAME = "FinanceReports AI Agent"

# Fixed fixture user who holds the toxic grant, named so the demo talk
# track can reference the same person every run.
TOXIC_GRANT_USER = {
    "first": "Priya",
    "last": "Shah",
    "department": "Marketing",
}


def stable_id(*parts: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "|".join(parts)))


def ensure_constraints(session) -> None:
    for label in (
        "GoogleWorkspaceTenant",
        "GoogleWorkspaceUser",
        "GoogleWorkspaceGroup",
        "GoogleWorkspaceOAuthApp",
    ):
        session.run(
            f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE"
        )


def merge_tenant(session, tenant_id: str, domain: str, name: str) -> None:
    session.run(
        """
        MERGE (t:GoogleWorkspaceTenant {id: $id})
        SET t.domain = $domain, t.name = $name, t.lastupdated = timestamp()
        """,
        id=tenant_id,
        domain=domain,
        name=name,
    )


def merge_group(session, tenant_id: str, group_id: str, name: str, domain: str) -> None:
    session.run(
        """
        MERGE (t:GoogleWorkspaceTenant {id: $tenant_id})
        MERGE (g:GoogleWorkspaceGroup {id: $id})
        SET g.name = $name, g.email = $email, g.lastupdated = timestamp()
        MERGE (t)-[:RESOURCE]->(g)
        """,
        tenant_id=tenant_id,
        id=group_id,
        name=name,
        email=f"{name.lower()}@{domain}",
    )


def merge_app(session, tenant_id: str, client_id: str, name: str) -> None:
    session.run(
        """
        MERGE (t:GoogleWorkspaceTenant {id: $tenant_id})
        MERGE (a:GoogleWorkspaceOAuthApp:ThirdPartyApp {id: $client_id})
        SET a.client_id = $client_id,
            a.display_text = $name,
            a.anonymous = false,
            a.native_app = false,
            a.lastupdated = timestamp()
        MERGE (t)-[:RESOURCE]->(a)
        """,
        tenant_id=tenant_id,
        client_id=client_id,
        name=name,
    )


def merge_user(
    session,
    tenant_id: str,
    group_id: str,
    user_id: str,
    email: str,
    first: str,
    last: str,
    is_admin: bool,
    department: str,
) -> None:
    session.run(
        """
        MERGE (t:GoogleWorkspaceTenant {id: $tenant_id})
        MERGE (g:GoogleWorkspaceGroup {id: $group_id})
        MERGE (u:GoogleWorkspaceUser {id: $id})
        SET u.primary_email = $email,
            u.email = $email,
            u.name = $name,
            u.given_name = $given_name,
            u.family_name = $family_name,
            u.is_admin = $is_admin,
            u.suspended = false,
            u.organization_department = $department,
            u.lastupdated = timestamp()
        MERGE (t)-[:RESOURCE]->(u)
        MERGE (u)-[:MEMBER_OF]->(g)
        """,
        tenant_id=tenant_id,
        group_id=group_id,
        id=user_id,
        email=email,
        name=f"{first} {last}",
        given_name=first,
        family_name=last,
        is_admin=is_admin,
        department=department,
    )


def merge_grant(session, user_id: str, app_id: str, scopes: list[str]) -> None:
    session.run(
        """
        MATCH (u:GoogleWorkspaceUser {id: $user_id})
        MATCH (a:GoogleWorkspaceOAuthApp {id: $app_id})
        MERGE (u)-[r:AUTHORIZED]->(a)
        SET r.scopes = $scopes, r.lastupdated = timestamp()
        """,
        user_id=user_id,
        app_id=app_id,
        scopes=scopes,
    )


def count_label(session, label: str) -> int:
    return session.run(f"MATCH (n:{label}) RETURN count(n) AS c").single()["c"]


def count_rel(session, rel: str) -> int:
    return session.run(f"MATCH ()-[r:{rel}]->() RETURN count(r) AS c").single()["c"]


def generate(driver, domain: str, tenant_name: str, max_users: int, seed: int) -> None:
    fake = Faker()
    Faker.seed(seed)

    tenant_id = stable_id("tenant", domain)

    with driver.session() as session:
        ensure_constraints(session)
        merge_tenant(session, tenant_id, domain, tenant_name)

        group_ids = {}
        for group_name in GROUPS:
            group_id = stable_id("group", domain, group_name)
            group_ids[group_name] = group_id
            merge_group(session, tenant_id, group_id, group_name, domain)

        app_ids = {}
        for app_name, _scopes, _toxic in APPS:
            client_id = stable_id("app", domain, app_name)
            app_ids[app_name] = client_id
            merge_app(session, tenant_id, client_id, app_name)

        toxic_scopes = next(s for n, s, _ in APPS if n == TOXIC_APP_NAME)
        toxic_app_id = app_ids[TOXIC_APP_NAME]
        low_risk_app_names = [n for n, _, toxic in APPS if not toxic]

        # Fixed fixture user for the toxic grant — created first, outside the
        # random loop, so it's always present regardless of --max-users.
        toxic_user_id = stable_id("user", domain, "fixture-toxic-grant")
        toxic_email = (
            f"{TOXIC_GRANT_USER['first'].lower()}."
            f"{TOXIC_GRANT_USER['last'].lower()}@{domain}"
        )
        merge_user(
            session,
            tenant_id,
            group_ids[TOXIC_GRANT_USER["department"]],
            toxic_user_id,
            toxic_email,
            TOXIC_GRANT_USER["first"],
            TOXIC_GRANT_USER["last"],
            is_admin=False,
            department=TOXIC_GRANT_USER["department"],
        )
        merge_grant(session, toxic_user_id, toxic_app_id, toxic_scopes)

        n_users = min(max_users, 200)  # hard ceiling regardless of flags/env
        for i in range(n_users):
            group_name = fake.random_element(GROUPS)
            is_admin = group_name == "IT-Admins" and fake.boolean(
                chance_of_getting_true=40
            )
            user_id = stable_id("user", domain, str(i))
            first = fake.first_name()
            last = fake.last_name()
            email = f"{first.lower()}.{last.lower()}{i}@{domain}"

            merge_user(
                session,
                tenant_id,
                group_ids[group_name],
                user_id,
                email,
                first,
                last,
                is_admin,
                group_name,
            )

            n_grants = fake.random_int(min=1, max=3)
            for app_name in fake.random_elements(
                low_risk_app_names, length=min(n_grants, len(low_risk_app_names)), unique=True
            ):
                scopes = next(s for n, s, _ in APPS if n == app_name)
                merge_grant(session, user_id, app_ids[app_name], scopes)

        print(
            f"Wrote {count_label(session, 'GoogleWorkspaceTenant')} tenant, "
            f"{count_label(session, 'GoogleWorkspaceUser')} users, "
            f"{count_label(session, 'GoogleWorkspaceGroup')} groups, "
            f"{count_label(session, 'GoogleWorkspaceOAuthApp')} apps, "
            f"{count_rel(session, 'AUTHORIZED')} OAuth grants."
        )
        print(
            f"Toxic grant: {toxic_email} <- '{TOXIC_APP_NAME}' scopes={toxic_scopes}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-users",
        type=int,
        default=int(os.environ.get("SYNTH_MAX_USERS", "25")),
        help="Cap on number of synthetic users, excluding the fixed toxic-grant "
        "fixture user (default from SYNTH_MAX_USERS or 25).",
    )
    parser.add_argument("--domain", default=os.environ.get("SYNTH_FAKE_DOMAIN", "demo-corp.test"))
    parser.add_argument("--tenant-name", default="Demo Corp")
    parser.add_argument("--seed", type=int, default=int(os.environ.get("SYNTH_SEED", "1337")))
    parser.add_argument("--neo4j-uri", default=os.environ.get("NEO4J_URI", "bolt://localhost:7687"))
    parser.add_argument("--neo4j-user", default=os.environ.get("NEO4J_USER", "neo4j"))
    parser.add_argument("--neo4j-password", default=os.environ.get("NEO4J_PASSWORD"))
    args = parser.parse_args()

    if not args.neo4j_password:
        print("NEO4J_PASSWORD not set (env or --neo4j-password required).", file=sys.stderr)
        sys.exit(1)

    if not args.domain.endswith(".test"):
        print(
            f"Refusing to write with non-synthetic-looking domain '{args.domain}' "
            "(expected a .test domain, per this repo's synthetic-data guardrail).",
            file=sys.stderr,
        )
        sys.exit(1)

    driver = GraphDatabase.driver(args.neo4j_uri, auth=(args.neo4j_user, args.neo4j_password))
    try:
        driver.verify_connectivity()
        generate(driver, args.domain, args.tenant_name, args.max_users, args.seed)
    finally:
        driver.close()


if __name__ == "__main__":
    main()
