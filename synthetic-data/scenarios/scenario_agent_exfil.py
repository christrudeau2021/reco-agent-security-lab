#!/usr/bin/env python3
"""
Scenario: an agent attempts an out-of-scope action, AIM blocks it (Phase 4).

Uses "support-chatbot" from generate_agents.py's fleet — granted only
ticket:read and ticket:write. This script:

  1. Performs an ALLOWED action (ticket:write) — succeeds, logged.
  2. Attempts a DENIED action (customer:export, an exfil-shaped capability
     support-chatbot was never granted) with auto_register=False — AIM
     denies it at the tool-call boundary, before the function body runs.

Requires: generate_agents.py already run (support-chatbot registered and
verified) and AIM's org enforcement mode set to "strict" (scripts/reset.sh
does both). In the default "monitoring" mode, step 2 would be silently
auto-granted instead of denied — see aim/README-local-build.md.

This is the scripted version of the exact deny scenario proven by hand in
Phase 2 (aim/quickstart/hello_agent_denied.py), now run against a fleet
agent instead of the throwaway quickstart one. It is the mechanism behind
the Phase 7 demo's "one agent being denied doing something it isn't"
moment — same code path, same server-side enforcement.
"""

import sys

from aim_sdk import secure
from aim_sdk.exceptions import ActionDeniedError

agent = secure("support-chatbot")


@agent.perform_action(capability="ticket:write")
def update_ticket(ticket_id: str, status: str) -> dict:
    return {"ticket_id": ticket_id, "status": status}


@agent.perform_action(capability="customer:export", auto_register=False)
def export_customer_data(segment: str) -> dict:
    # Exfil-shaped: a support chatbot has no business bulk-exporting the
    # customer table. If this line ever runs, the deny failed.
    return {"segment": segment, "exported_rows": 50000}


def main() -> int:
    print("=== ALLOWED: support-chatbot uses its granted ticket:write ===")
    result = update_ticket("TICKET-4821", "resolved")
    print(f"  -> succeeded: {result}\n")

    print("=== DENIED: support-chatbot attempts customer:export (not granted) ===")
    try:
        result = export_customer_data("enterprise")
        print(f"  -> UNEXPECTED SUCCESS: {result}", file=sys.stderr)
        print(
            "  This should have been denied — check org enforcement mode is "
            "'strict' (see aim/README-local-build.md) and that support-chatbot "
            "is verified in the dashboard.",
            file=sys.stderr,
        )
        return 1
    except ActionDeniedError as e:
        print(f"  -> denied, as expected: {e}\n")

    print("Scenario complete: one allowed action executed, one denied action")
    print("blocked before it ran. Check the AIM dashboard's Security tab for")
    print("the live audit trail entry.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
