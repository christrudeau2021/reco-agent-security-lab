#!/usr/bin/env python3
"""
Synthetic AI agent fleet generator (Phase 4).

Registers a small fleet of synthetic AI agents in AIM (Agent Identity
Management), each with a minimal, explicit capability grant — deny-by-
default, per CLAUDE.md's Agent Behavior guardrail. One agent is deliberately
over-permissioned (broad admin-style capabilities unrelated to its stated
job) to mirror the toxic-OAuth-grant pattern already seeded on the identity
side by generate_identities.py.

Requires:
  - The AIM stack up and healthy (docker compose up -d aim-backend ...)
  - An authenticated aim-sdk session (see aim/README-local-build.md — the
    published OAuth login flow doesn't work self-hosted; hand-write
    ~/.aim/sdk_credentials.json from a direct login API call, or run this
    after scripts/reset.sh, which does the bootstrap for you)

After registering each agent this script also verifies it via AIM's admin
API (POST /api/v1/agents/{id}/verify) — a freshly-registered agent is
"pending", and in strict enforcement mode a pending/unverified agent is
denied everything regardless of its capability grants (see Phase 2 notes
in aim/README-local-build.md), so an unverified fleet would make every
scenario script fail for the wrong reason.

Capped by --max-agents (SYNTH_MAX_AGENTS in .env) — this is a fixed roster
below, so the cap only matters if you shrink it; it will never grow past
the roster's own length.
"""

import argparse
import os
import sys

import requests
from aim_sdk import secure

# (name, capabilities, description, department, over_permissioned)
FLEET = [
    (
        "finance-reporting-bot",
        ["db:read", "finance:read"],
        "Generates weekly finance summary reports from the warehouse.",
        "Finance",
        False,
    ),
    (
        "support-chatbot",
        ["ticket:read", "ticket:write"],
        "Customer support chatbot that reads and updates support tickets.",
        "Support",
        False,
    ),
    (
        "recruiting-assistant",
        ["candidate:read"],
        "Screens inbound candidate applications and summarizes resumes.",
        "People",
        False,
    ),
    (
        "devops-deploy-agent",
        ["deploy:read"],
        "Reports on deployment status; intentionally not granted deploy:execute.",
        "Engineering",
        False,
    ),
    (
        "marketing-content-agent",
        ["content:write"],
        "Drafts marketing copy for review before publishing.",
        "Marketing",
        False,
    ),
    (
        # Deliberately over-permissioned: broad admin-style capability with
        # no relation to its stated job, same shape as the toxic OAuth grant
        # generate_identities.py plants on the identity side.
        "legacy-integration-agent",
        ["db:read", "file:read", "admin:full_access"],
        "Undocumented legacy sync job nobody remembers the original scope for.",
        "Engineering",
        True,
    ),
]


def verify_agent(base_url: str, access_token: str, agent_id: str) -> None:
    resp = requests.post(
        f"{base_url}/api/v1/agents/{agent_id}/verify",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    resp.raise_for_status()


def get_admin_access_token(base_url: str, email: str, password: str) -> str:
    resp = requests.post(
        f"{base_url}/api/v1/public/login",
        json={"email": email, "password": password},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["accessToken"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-agents",
        type=int,
        default=int(os.environ.get("SYNTH_MAX_AGENTS", str(len(FLEET)))),
    )
    parser.add_argument(
        "--aim-url", default=f"http://localhost:{os.environ.get('AIM_BACKEND_PORT', '8090')}"
    )
    parser.add_argument("--admin-email", default=os.environ.get("AIM_ADMIN_EMAIL", "admin@opena2a.org"))
    parser.add_argument("--admin-password", default=os.environ.get("AIM_ADMIN_PASSWORD"))
    args = parser.parse_args()

    if not args.admin_password:
        print("AIM_ADMIN_PASSWORD not set (env or --admin-password required).", file=sys.stderr)
        sys.exit(1)

    access_token = get_admin_access_token(args.aim_url, args.admin_email, args.admin_password)

    roster = FLEET[: max(0, min(args.max_agents, len(FLEET)))]
    registered = []
    for name, capabilities, description, department, over_permissioned in roster:
        agent = secure(
            name,
            capabilities=capabilities,
            description=description,
            metadata={"department": department, "synthetic": True},
        )
        verify_agent(args.aim_url, access_token, agent.agent_id)
        registered.append((name, capabilities, over_permissioned))
        flag = " [OVER-PERMISSIONED]" if over_permissioned else ""
        print(f"Registered + verified: {name} -> {capabilities}{flag}")

    print(f"\n{len(registered)} agents registered and verified.")


if __name__ == "__main__":
    main()
