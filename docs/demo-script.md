# Demo script — plain-English version

This explains what you built, in normal words, and gives you a talk
track to run it live. No jargon without an explanation first.

## The big idea, in one paragraph

Companies give a LOT of people and apps access to their stuff — Google
Drive, Slack, Salesforce, whatever. Some of those "people" aren't
people anymore — they're AI agents that can read files, send emails,
approve things, on their own. Nobody has a clean map of who (or what)
can touch what, and almost nobody has a way to stop an AI agent the
instant it tries to do something it shouldn't. This project builds a
small, working version of that map-and-stop-button, using real
open-source software, so you can show it instead of just describing it.

## What's actually real here (say this early, every time)

Three moving parts, wired together:

1. **A graph database (Neo4j)** holding a map of users, groups, apps,
   and "who can access what." Think of it like a family tree, but
   instead of parents and children, the connections are "this person is
   in this group," "this app was granted access to this data." A graph
   database is just a database built to store connections like that
   well, instead of forcing everything into spreadsheet rows.
2. **An AI agent guard (AIM)** that AI agents have to check in with
   before doing anything. Every agent gets a fixed list of things it's
   allowed to do — like a hall pass that only works for specific rooms.
   If it tries to do something not on its list, it gets denied, and
   that denial gets written down.
3. **A dashboard** (the thing you'll actually click through) that reads
   from both of those and shows it in one place, organized as
   Discover → Prioritize → Remediate — find what exists, figure out
   what's risky, decide what to do about it.

The graph database software and the agent guard software are both
real, working, open-source tools — not something built from scratch for
this demo. What's synthetic is the *data* — fake users like
`priya.shah@demo-corp.test`, fake companies, fake AI agents. No real
person's data is anywhere in this.

## The walkthrough (5-10 minutes)

Before you start: run `./scripts/demo.sh` — it resets everything,
reloads the data, and checks all three pieces are actually up. It
prints the UI's URL when it's done. Don't start clicking until it says
"Stack is up and seeded."

### 1. Discover tab — "what exists?"

Open the UI. First tab, already selected. Say something like:

> "This is the map. Top box is every user, group, and third-party app
> connected to this company's Google Workspace — that data came from a
> synthetic generator, but it's stored exactly the way a real scan
> would store it. Middle box is the AI agents — six of them, each with
> a short list of things they're allowed to do. Bottom box is a real
> GitHub organization's repos, pulled live from GitHub's API, just to
> prove the map-building part of this works against something real,
> not just fake data."

Click open "26 users" to show the list is really there, not just a
count on a card.

### 2. Prioritize tab — "what's actually risky?"

Click the second tab. Say:

> "Same information, but now sorted by how bad it is. This isn't some
> fancy AI risk score — it's a simple rule: if something has admin-level
> or finance-level access and doesn't obviously need it, it goes to the
> top. Simple on purpose — the point is proving the pipeline works, not
> showing off a scoring algorithm."

Point at the top finding — the marketing employee whose AI agent
somehow got both broad Google Drive access AND a finance-admin-shaped
permission. Say:

> "This is what a security team calls a 'toxic combination' — nothing
> here is a bug or a hack, every one of these permissions was granted
> normally, by someone clicking 'allow.' The risk is that nobody
> connected the dots that *together* they're a problem."

### 3. The centerpiece — watch an AI agent get blocked, live

This is the moment to slow down for. Say:

> "Everything so far was 'here's a map.' This part is 'here's a
> guard.' I'm going to run one script that makes a real AI agent do two
> things: one thing it's allowed to do, and one thing it's not."

Run this in a terminal, in front of them:

```bash
cd reco-agent-security-lab
source .venv-aim-sdk/bin/activate
python synthetic-data/scenarios/scenario_agent_exfil.py
```

Narrate as it prints:

> "First line — the support chatbot writes a support ticket. That's on
> its allowed list, so it goes through. Second line — same agent, same
> code, tries to export customer data. That's NOT on its list. Watch —
> it gets denied, in real time, by the actual guard software, not a
> fake message I wrote."

Then flip back to the dashboard's Remediate tab and scroll to "Audit
trail (real, from AIM)" — point out the denied attempt is sitting
there, timestamped, with the agent's name and exactly what it tried.

> "That's the proof point. It's not enough to say 'we have policies' —
> you need a system that actually enforces them, and a paper trail
> showing it did."

### 4. Remediate tab — "what would we do about it?"

Say:

> "These 'Revoke' buttons are intentionally fake for this demo — they
> just log what *would* happen locally, they don't call any real API.
> The reason is I don't want to actually revoke access in someone's
> real Google Workspace or AI agent platform from a demo script. In a
> real product, this button would call the real API and this would
> actually happen."

### 5. Wrap-up line

> "So: real graph database, real agent-guard software, real denial
> caught in a real audit log, wired to a synthetic company so nothing
> about this touches anyone's real data. That's the whole loop — see
> what exists, see what's risky, stop the bad thing, prove you stopped
> it."

## Anticipated questions (plain answers)

**"Is this what [Reco] actually sells?"**
No — this proves I understand the shape of the problem they solve
(mapping identity/access/agent risk and enforcing it), using different,
open-source tools. It's a study project, not a copy of their product.

**"Could this actually protect a real company?"**
Not as-is — no security review, no scale testing, no real integrations
built. It's a learning lab, not a product.

**"What's fake and what's real, one more time?"**
Real: the graph database software, the agent-guard software, the
GitHub data, the denial you just watched happen. Fake: the company, the
users, the specific AI agents, and the "Revoke" button's action.

## If something breaks mid-demo

Don't debug live. Say "let me show you the trail instead" and open the
Remediate tab's audit trail table, or fall back to the Neo4j browser at
`localhost:7474` and run:

```cypher
MATCH (n) RETURN labels(n)[0] AS type, count(*) AS count ORDER BY type
```

That always shows *something* real even if a script fails.
