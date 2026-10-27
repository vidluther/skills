# Conventions

A cheat sheet for future me (and anyone new): what the jargon means, and which skills to reach for when.

## Intent

I've found it's better to tell the agent *what* I want to accomplish, not *how*. It also lets me check at the end whether we met the goal.

Where ISA lives in the skills: `marshal` records where ISAs go, `rubber-duck` writes them (format: [`skills/rubber-duck/ISA-FORMAT.md`](./skills/rubber-duck/ISA-FORMAT.md)), `reconcile-plans` merges multi-model drafts into one, `to-issues` slices them so each issue cites its ISCs, and `isa-check` runs the evals to tell us whether we're done.

## Glossary

### Intent

| Term | Means | Remember it as |
| --- | --- | --- |
| **ISA** — Ideal State Artifact | One doc per **initiative** describing what "done" looks like: ideal state, constraints, decisions, ISCs, status. The source of truth — code is judged against it. | "The picture in my head, written down." |
| **ISC** — Ideal State Criterion | One atomic, testable statement inside an ISA (`ISC-3 — booking takes ≤3 taps`). Each has an eval. | "One checkbox on the picture." |
| **Eval** | How an ISC is checked. Cheapest that works: assert → test → question set → LLM judge. | "How I'd know it passed." |
| **Eval ladder** | That cheap→expensive order. Objective ISCs use code; subjective ones use a model judge. | "Climb only as high as you need." |
| **Decisions log** | Dated lines in the ISA: what changed in the ideal state, and why. | "Changed my mind? Write it here, not in code." |
| **Parent / child ISA** | Big project = parent ISA (overall intent, shared constraints) + child ISA per major intent. | "Epic → sub-epics." |
| **Initiative vs issue** | Initiative = unit of **intent** (gets an ISA). Issue = unit of **work** (cites ISCs, no ISA of its own). | "ISA per goal, not per ticket." |

Origin: Daniel Miessler, [Writing is closer to thought than code](https://danielmiessler.com/blog/writing-is-closer-to-thought-than-code).

### Planning

| Term | Means |
| --- | --- |
| **Rubber-duck / grilling** | `rubber-duck` interviews me in numbered rounds until every decision is made. Answer like "1 yes, 3 no, 4 let's talk." |
| **Frontier** | The questions answerable *now* — everything whose prerequisites are settled. One round = the whole frontier. |
| **ADR test** | Is it hard to reverse, surprising, or a real trade-off? If yes → worth an ADR and worth planning on multiple models. If no → one plan is enough. |
| **Reconcile / council** | `reconcile-plans` merges plans from different models: settled / majority / divergent / unique catches / blind spots. A council = parallel reviewers, one lens each, plans anonymized. |

### Issues

| Term | Means |
| --- | --- |
| **Tracer bullet / vertical slice** | An issue that cuts through every layer (schema → API → UI → tests) thinly, so it's demoable alone. Preferred over horizontal "do all the DB work" issues. |
| **AFK / HITL** | AFK = an agent can do it unattended. HITL = human in the loop (design call, review, manual test). Applied as labels. |
| **Spike** | First slice when we're guessing how something external behaves. Build the smallest probe, write down what we learned. |
| **Wide refactor / expand–contract** | A mechanical change that breaks everything at once. Expand (add new beside old) → migrate in batches → contract (delete old). |
| **Triage labels** | State (`needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`), provenance (`new` = agent-created), category (`bug`, `enhancement`). |

### Repo docs

| File | Holds |
| --- | --- |
| `AGENTS.md` / `CLAUDE.md` | Rules agents read every session. One canonical file. |
| `CONTEXT.md` | Domain glossary — the words this project uses. `CONTEXT-MAP.md` if multiple contexts. |
| `docs/adr/` | Architecture Decision Records — why we chose X. |
| `docs/isa/` | ISAs, when they live in-repo. |
| `docs/agents/` | What `marshal` recorded: tracker, labels, domain layout, ISA location. |
| `.out-of-scope/` | Rejected requests, with reasons. |

### This harness

| Term | Means |
| --- | --- |
| **Vendored skill** | Forked from a third party (has `source:` in frontmatter). Ours now — never auto-updated; review with `./update-thirdparty-skills.sh <name>`. |
| **TWG skills** | `twg*` — Atlassian skills installed by the `twg` CLI. Gitignored; update with `twg upgrade` + `./setup.sh`. |
| **`marshal`** | Lays a repo's rails once, so every other skill knows the tracker, labels, docs, style, and VCS. |

## Workflows

### New repo, or a repo agents haven't touched

1. `/marshal` — answer its rounds.
2. Done. Re-run only when a convention changes.

### Plan an initiative

1. `/rubber-duck <the idea>` — answer rounds until the frontier is empty. It steers toward ideal state → constraints → ISCs with evals.
2. It saves the ISA where `docs/agents/isa.md` says (default `docs/isa/<topic>.md`). External (Confluence/Jira) → it shows a draft first.
3. Passes the ADR test? Drafts go to `docs/plans/<model>-<topic>.md` instead; run step 1 on another model, then `/reconcile-plans <topic>` writes the final ISA.
4. `/to-issues` — slices the ISA; each issue cites its ISCs, and their evals become acceptance checks. It flags any ISC no issue covers.

### Big work project with several intents

1. Parent ISA first: overall ideal state + constraints that apply everywhere.
2. One child ISA per major intent, each linking `Parent:`.
3. `/to-issues` per child ISA, not per parent.
4. Something in an issue turns out to need its own trade-offs? Promote it to a child ISA.

### Change your mind mid-build

1. `/rubber-duck` on the existing ISA — it updates in place and logs a dated Decisions entry.
2. Don't renumber ISCs; dropped ones stay struck through.
3. Affected issues? `/to-issues` again for the gap.

### Are we done?

1. `/isa-check <topic>` — runs each ISC's eval (cheapest rung first), reports pass / fail / untested with evidence, then offers to update the ISA's Status.
2. Failures → `/to-issues` for the gap. An ISC that turned out wrong → `/rubber-duck` it (dated Decisions entry).
3. All pass → `/improve-codebase-architecture` before shipping.

### Pick up an issue

1. Read the ISA it belongs to (via its **Satisfies** line / epic / parent link).
2. Implement. If it contradicts a constraint or decision → stop and say so.
3. Changed your mind about the goal? Add a dated Decisions entry first.

### Review someone else's PR

1. Small PR: read it yourself first, then `/review-pr <url>` for a second pass.
2. Big or unfamiliar PR: `/review-pr <url>` first — digest gives the why, a change map, an intent check against the ticket/ISA, then findings.
3. Open the links, decide. To post one: "post 2" (it shows the text first).
4. New review habit? Add a line to `skills/review-pr/REVIEW-CONVENTIONS.md`.

### Something's broken

1. `/diagnose` — reproduce → minimise → hypothesise → instrument → fix → regression test.

### Lost in unfamiliar code

1. `/zoom-out` — purpose, modules, callers, dependencies, where to start reading.

### Code feels tangled

1. `/improve-codebase-architecture` — finds deepening opportunities using `CONTEXT.md` + ADRs.
2. Worth doing? `/to-issues` on the result.

### Weekly hygiene (work)

1. `twg-status-rollups` — what I did this week / standup material.
2. `twg-jira-resolve-merged-work` — dry run to find tickets merged but not closed.
3. `remctl` — park ISC follow-ups and "revisit this decision" as Reminders.
