# Capability policy

CLAUDE.md originally scoped this directory for standalone policy YAML
files. That's not how AIM's self-hosted deny-by-default actually works —
there's no local policy file AIM reads. The real mechanism is:

- **Org enforcement mode** — `strict` (deny unless explicitly granted),
  flipped via `PUT /api/v1/admin/enforcement-settings` in
  `scripts/reset.sh`. Default is `monitoring` (auto-grant), which is
  permissive and wrong for a "deny-by-default" demo — see
  `aim/README-local-build.md`.
- **Per-agent capability grants** — each synthetic agent registers with
  an explicit, minimal `capabilities` list via `secure()` in
  `synthetic-data/generate_agents.py`. Anything not in that list is
  denied in strict mode.
- **Verification gate** — a newly registered agent is `pending` and
  denied everything regardless of capability grants until verified
  (`POST /api/v1/agents/{id}/verify`), also handled in
  `generate_agents.py`.

The proof this works end-to-end is
`synthetic-data/scenarios/scenario_agent_exfil.py`: `support-chatbot`
succeeds at its granted `ticket:write` and is denied the ungranted
`customer:export`.
