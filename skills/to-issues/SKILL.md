---
name: to-issues
description: Break a plan, spec, or PRD into independently-grabbable issues on the project issue tracker using tracer-bullet vertical slices. Use when user wants to convert a plan into issues, create implementation tickets, or break down work into issues.
---

# To Issues

Break a plan into independently-grabbable issues using vertical slices (tracer bullets).

The issue tracker and triage label vocabulary should have been provided to you — run the `marshal` skill if not.

## Process

### 1. Gather context

Work from whatever is already in the conversation context. If the user passes an issue reference (issue number, URL, or path) as an argument, fetch it from the issue tracker and read its full body and comments.

If the source is an **ISA** (Ideal State Artifact — see `docs/agents/isa.md` for where they live), read it in full: its ISCs are the definition of done for every slice, its constraints bind every slice (they stay on the ISA or epic; never copy them into each issue), and its Decisions log overrides anything older in the conversation. An ISA is sliced per initiative — for a parent ISA with child ISAs, slice each child, not the parent. If the user passes a plan that clearly describes an initiative but there's no ISA, say so and offer `rubber-duck` to write one first; proceed without it only if they decline.

### 2. Explore the codebase (optional)

If you have not already explored the codebase, do so to understand the current state of the code. Issue titles and descriptions should use the project's domain glossary vocabulary, and respect ADRs in the area you're touching.

Look for opportunities to prefactor the code to make the implementation easier. "Make the change easy, then make the easy change."

### 3. Probe the tracker's native fields

Before drafting, discover what this project's tracker natively supports: issue types, labels, priority, and sizing (Linear's estimate field, if enabled for the team; Jira story points or custom fields such as t-shirt size — check the issue type's field metadata; GitHub labels and Projects fields).

Metadata goes in native fields, never in body prose. Only data with no native home earns a body header line (e.g. **Repo:** / **Files:** in a multi-repo project). If the tracker has no sizing field, omit sizing entirely — free-form metadata text just takes up space. HITL/AFK is expressed as the work-type label (`hitl` / `afk`, mapped in the triage-labels doc), never in the body.

Links between issues follow the same rule: use the native field when it exists, a one-line header only when it doesn't, and never write a value that says "none".

| Thing | Jira / Linear | GitHub Issues | Local files (`issues/NNNN-slug.md`) |
| --- | --- | --- | --- |
| Type (`afk` / `hitl`, bug) | Labels and issue type | Labels | In the status line |
| Parent | Native parent field | Sub-issues if the repo uses them; otherwise omit | Omit; `issues/README.md` is a flat index |
| Dependencies | Native "blocks" link | `Blocked by: #14` line, only when blocked | `Blocked by: 0003` in the status line, only when blocked |
| Sub-tasks | Native sub-tasks; the parent Story links them | Flat issues unless the repo uses sub-issues | Flat files, one per slice |
| Spec | One-line footer | One-line footer | One-line footer, omitted if there's no ISA |

A local issue file starts like this, and nothing else goes above **What**:

```markdown
# 0004 Add Needs EOB status to report-workorders

Status: open · Type: afk · Blocked by: 0002
```

### 4. Draft vertical slices

Break the plan into **tracer bullet** issues. Each issue is a thin vertical slice that cuts through ALL integration layers end-to-end, NOT a horizontal slice of one layer.

Slices may be 'HITL' or 'AFK'. HITL slices require human interaction, such as an architectural decision or a design review. AFK slices can be implemented and merged without human interaction. Prefer AFK over HITL where possible.

<vertical-slice-rules>
- Each slice delivers a narrow but COMPLETE path through every layer (schema, API, UI, tests)
- A completed slice is demoable or verifiable on its own
- Each slice is sized to fit in a single fresh context window
- Prefer many thin slices over few thick ones
- Any prefactoring should be done first
- From an ISA: each slice cites the ISC IDs it satisfies (fully or partly), and every ISC is covered by at least one slice
</vertical-slice-rules>

**Stories and sub-tasks.** When the tracker has a hierarchy and the work needs it, a **Story** is one outcome (usually one ISC) and its **sub-tasks** are the slices. The Story says What and Why, links its sub-tasks, and keeps only story-level checks ("sub-tasks X and Y are done, and one end-to-end run passes"). The detailed checks live on each sub-task. Never copy a sub-task's checklist onto its Story. Without a hierarchy (most GitHub repos, local files), every slice is a flat issue.

**Coverage check (ISA source only).** Before quizzing, map ISCs → slices. An ISC no slice covers is a gap — add a slice or flag it. A slice that covers no ISC is either prefactoring/spike work (fine — say so) or scope the ISA doesn't ask for (flag it; the ISA wins, or the user adds a Decisions entry). Don't split an ISC across slices so finely that no single slice can run its eval.

**Prefer a spike when the plan rests on unverified assumptions.** If neither the plan nor the team has verified how an external system actually behaves (an undocumented API, a third-party app's real payloads, a retry policy nobody has observed), don't write implementation slices on top of the guess. The first slice manufactures the missing knowledge — stand up the smallest thing that lets you observe reality (a minimal server capturing real requests, a probe script) and write down what you learn. Downstream slices then build on evidence instead of assumed expertise.

**Wide refactors are the exception to vertical slicing.** A **wide refactor** is one mechanical change — rename a column, retype a shared symbol — whose **blast radius** fans across the whole codebase, so a single edit breaks thousands of call sites at once and no vertical slice can land green. Don't force it into a tracer bullet; sequence it as **expand–contract**. First expand: add the new form beside the old so nothing breaks. Then migrate the call sites over in batches sized by blast radius (per package, per directory), each batch its own issue blocked by the expand, keeping CI green batch to batch because the old form still exists. Finally contract: delete the old form once no caller remains, in an issue blocked by every migrate batch. When even the batches can't stay green alone, keep the sequence but let them share an integration branch that all block a final integrate-and-verify issue — green is promised only there.

### 5. Quiz the user

Present the proposed breakdown as a numbered list. For each slice, show:

- **Title**: short descriptive name
- **Shape**: Task / Bug / Spike (see the templates below)
- **Type**: HITL / AFK (as a label)
- **Native fields**: proposed estimate, labels, priority — whatever step 3 found
- **Parent**: the Story it belongs to, if the tracker has a hierarchy
- **Blocked by**: which other slices (if any) must complete first
- **User stories covered**: which user stories this addresses (if the source material has them)
- **ISCs satisfied**: which ISC IDs this slice satisfies (if the source is an ISA)

With an ISA source, follow the list with the coverage map: each ISC → the slices that satisfy it, with any uncovered ISC or ISC-less slice called out.

Ask the user:

- Does the granularity feel right? (too coarse / too fine)
- Are the dependency relationships correct?
- Should any slices be merged or split further?
- Are the correct slices marked as HITL and AFK?
- Are the shapes and field values right?

Iterate until the user approves the breakdown.

### 6. Publish the issues to the issue tracker

**Translate, don't transcribe.** The reader is an experienced software developer who joined the project today: they have not seen the source plan, the planning conversation, or any of its shorthand. Every issue must stand alone.

- The plan supplies decisions and evidence — never sentences. Re-derive each issue in your own words, after checking the actual state of the repo.
- Concise beats complete. Self-contained doesn't mean exhaustive: 2–4 sentences of context, tight bullets, one explanation per fact. Every sentence must change what the assignee does or how they verify it — cut anything else.
- Explain every citation in one plain sentence instead of name-dropping it. "About 13% of workouts arrive with a corrupted heart-rate series (upstream bug HAE #60)" — never "HAE #60: …". This applies to upstream issue numbers, review findings, and ADRs alike.
- Specificity scales with code maturity. Cite file paths, line numbers, and real snippets only for code that exists and that you verified while drafting — a concrete `dashboard.controller.js:56` saves the assignee rediscovery. For greenfield work, describe end-to-end behavior and contracts instead. Never invent paths.
- If a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it and note briefly that it came from a prototype. Trim to the decision-rich parts.

**Write plain English, like a teammate, not a spec.**

- Name the real thing: the payer, the person, the file, the prompt. Never abstract roles ("the Owner", "the target system", "the orchestration layer").
- One check per bullet, written as what happens. No noun piles ("verification, holds, selected claims, and closing are correct").
- Everyday words over spec jargon: "keep every run", not "preserve execution provenance"; "the call as it happened", not "first-pass qualification evidence". When a project term is unavoidable, link the project's glossary once.
- No unrequested clarifying asides ("code sends the digits; an AI never does"). They're often wrong and read as filler.
- If something is genuinely undecided, add an **Open question** section with the question, rather than vague wording around it.
- Project-wide rules (operating limits, data handling, approval rules) live on the epic or ISA. Don't repeat them in each issue.

For each approved slice, publish a new issue using the matching template below. Set metadata (type, estimate, priority, HITL/AFK, parent, dependencies) through the native fields found in step 3, or the status line for local files. Apply the `new` provenance label where the tracker has labels, so each issue is identifiable as agent-created. They enter the inbox state automatically (no state label means inbox).

Publish issues in dependency order (blockers first) so links point at real identifiers. Every template ends with one footer line, and only the parts that apply:

`Spec: <ISA link or path> (ISC-4) · Terms: <glossary link>`

Don't restate the ISC in a separate section: its eval already appears in **Done when**, phrased as the check to run.

<task-template>
## What

1–3 plain sentences: what this issue builds or changes, starting with a verb. For a Story, also list its sub-tasks here, one line each.

## Why

1–3 sentences: what's broken, missing, or manual today, and what in the code or process is in the way. Cite `path/file:line` when it exists.

## Done when

- One checkable outcome per bullet, something a person can tick off
- …

## Not in this ticket

One line naming nearby work that belongs elsewhere, with its issue IDs. Omit if there's nothing worth naming.
</task-template>

<bug-template>
## What's broken

The defect in plain English, anchored to the offending `path/file:line` (the code exists by definition).

## How to reproduce

1. Numbered steps from a clean start
2. …
3. Observed vs expected result

## Fix

The known or suspected remedy, and why it's safe for existing callers.

## Done when

- The broken case now works
- Existing callers of the touched code still pass
</bug-template>

<spike-template>
## Question

The specific unknown, and why guessing is riskier than finding out.

## How to find out

The concrete method: stand up a minimal server and capture real requests, run a probe against the live API, read the vendor's actual responses.

## Done when

- The findings or decision are written down where downstream issues can cite them
- Small enabling code (such as the capture harness) may land; shipped features don't
</spike-template>

Do NOT close or modify any parent issue.

---

*Inspired by the `to-tickets` skill in [mattpocock/skills](https://github.com/mattpocock/skills); this version has diverged enough to be maintained independently.*
