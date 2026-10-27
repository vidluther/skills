# Ideal State Artifacts (ISA)

How skills should find, write, and consume this repo's intent documents.

An ISA is the written source of truth for what an initiative should become — closer to intent than the code. Implementations are judged against the ISA, not against the previous draft. If the code drifts, rebuild against the ISA instead of patching.

## One ISA per initiative

- **ISA = unit of intent** — something you'd judge "done" as a whole (an epic, a project, a feature with its own constraints and trade-offs). Not one per repo, not one per issue.
- **Issue = unit of work** — `to-issues` slices an ISA into issues. Each issue cites the ISC IDs it satisfies, and their evals become its acceptance/testing criteria. Issues don't get their own ISA.
- **An issue that grows its own intent** (its own ideal state, constraints, trade-offs) is really a sub-initiative: give it a small child ISA that links its parent and inherits the parent's constraints.
- **Large projects** get a parent ISA (overall ideal state, cross-cutting constraints) plus one child ISA per major intent.

## Shape

```markdown
# <Initiative> — ISA

Parent: <link, if this is a child ISA>

## Ideal State
<prose — what it's like when this is done>

## Constraints
- <must not / must respect>

## Decisions
- YYYY-MM-DD — <what changed in the ideal state> — <why>

## Ideal State Criteria
- ISC-1 — <atomic, testable criterion> — eval: <assert | test | question set | LLM judge>

## Status
- ISC-1 — pass | fail | untested
```

Change your mind → add a dated Decisions entry and edit the ideal state. Don't bury the change in code. Never renumber ISCs — issues cite them; dropped ones stay struck through.

## Where ISAs live

<!-- marshal fills this in: one of the layouts below -->

**In-repo** — `docs/isa/<topic>.md`, `<topic>` a kebab-case slug. Child ISAs link their parent by relative path.

**External** — <Confluence space / parent page, or "Jira epic description">. The repo keeps no copy (two copies drift); link the ISA from each issue instead.

**Split** — parent ISA external (<location>), child ISAs in-repo at `docs/isa/<topic>.md`, each with a `Parent:` link.

## Before working on an issue

Find the ISA the issue belongs to (its `ISC-n` references, its epic, or its `Parent:` link) and read it. If none exists, **proceed silently** — don't create one unprompted. `rubber-duck` produces ISAs when an initiative is actually planned.

If your change contradicts a constraint or decision in the ISA, surface it rather than silently overriding.
