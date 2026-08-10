---
name: to-issues
description: Break a plan, spec, or PRD into independently-grabbable issues on the project issue tracker using tracer-bullet vertical slices. Use when user wants to convert a plan into issues, create implementation tickets, or break down work into issues.
---

# To Issues

Break a plan into independently-grabbable issues using vertical slices (tracer bullets).

The issue tracker and triage label vocabulary should have been provided to you — run `/marshal` if not.

## Process

### 1. Gather context

Work from whatever is already in the conversation context. If the user passes an issue reference (issue number, URL, or path) as an argument, fetch it from the issue tracker and read its full body and comments.

### 2. Explore the codebase (optional)

If you have not already explored the codebase, do so to understand the current state of the code. Issue titles and descriptions should use the project's domain glossary vocabulary, and respect ADRs in the area you're touching.

Look for opportunities to prefactor the code to make the implementation easier. "Make the change easy, then make the easy change."

### 3. Probe the tracker's native fields

Before drafting, discover what this project's tracker natively supports: issue types, labels, priority, and sizing (Linear's estimate field, if enabled for the team; Jira story points or custom fields such as t-shirt size — check the issue type's field metadata; GitHub labels and Projects fields).

Metadata goes in native fields, never in body prose. Only data with no native home earns a body header line (e.g. **Repo:** / **Files:** in a multi-repo project). If the tracker has no sizing field, omit sizing entirely — free-form metadata text just takes up space. HITL/AFK is expressed as a label, never in the body.

### 4. Draft vertical slices

Break the plan into **tracer bullet** issues. Each issue is a thin vertical slice that cuts through ALL integration layers end-to-end, NOT a horizontal slice of one layer.

Slices may be 'HITL' or 'AFK'. HITL slices require human interaction, such as an architectural decision or a design review. AFK slices can be implemented and merged without human interaction. Prefer AFK over HITL where possible.

<vertical-slice-rules>
- Each slice delivers a narrow but COMPLETE path through every layer (schema, API, UI, tests)
- A completed slice is demoable or verifiable on its own
- Each slice is sized to fit in a single fresh context window
- Prefer many thin slices over few thick ones
- Any prefactoring should be done first
</vertical-slice-rules>

**Prefer a spike when the plan rests on unverified assumptions.** If neither the plan nor the team has verified how an external system actually behaves (an undocumented API, a third-party app's real payloads, a retry policy nobody has observed), don't write implementation slices on top of the guess. The first slice manufactures the missing knowledge — stand up the smallest thing that lets you observe reality (a minimal server capturing real requests, a probe script) and write down what you learn. Downstream slices then build on evidence instead of assumed expertise.

**Wide refactors are the exception to vertical slicing.** A **wide refactor** is one mechanical change — rename a column, retype a shared symbol — whose **blast radius** fans across the whole codebase, so a single edit breaks thousands of call sites at once and no vertical slice can land green. Don't force it into a tracer bullet; sequence it as **expand–contract**. First expand: add the new form beside the old so nothing breaks. Then migrate the call sites over in batches sized by blast radius (per package, per directory), each batch its own issue blocked by the expand, keeping CI green batch to batch because the old form still exists. Finally contract: delete the old form once no caller remains, in an issue blocked by every migrate batch. When even the batches can't stay green alone, keep the sequence but let them share an integration branch that all block a final integrate-and-verify issue — green is promised only there.

### 5. Quiz the user

Present the proposed breakdown as a numbered list. For each slice, show:

- **Title**: short descriptive name
- **Shape**: Task / Bug / Spike (see the templates below)
- **Type**: HITL / AFK (as a label)
- **Native fields**: proposed estimate, labels, priority — whatever step 3 found
- **Blocked by**: which other slices (if any) must complete first
- **User stories covered**: which user stories this addresses (if the source material has them)

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

For each approved slice, publish a new issue using the matching template below. Set metadata (estimate, priority, HITL/AFK) through the native fields found in step 3. Apply the `new` provenance label so each issue is identifiable as agent-created. They enter the inbox state automatically (no state label means inbox).

Publish issues in dependency order (blockers first) so you can reference real issue identifiers in the "Blocked by" field. Every shape ends with:

- **Blocked by** — real issue identifiers, or "None — can start immediately".
- **Parent** — reference to the parent issue, only if the source was an existing issue.

<task-template>
**Context**

What exists today and why this work is needed — self-contained, 2–5 plain sentences. A reader must be able to judge the acceptance criteria from this section alone.

**Scope**

What to do, described as end-to-end behavior. Include an explicit non-goals line: what this issue deliberately does NOT touch, so the work doesn't sprawl.

**Acceptance**

- Observable outcome 1
- Observable outcome 2
</task-template>

<bug-template>
**Problem**

The defect, with the offending code/paths (the code exists by definition — anchor it).

**Reproduction**

1. Numbered steps from a clean start
2. …
3. Observed vs expected result

**Fix**

The known or suspected remedy, and why it's safe for existing consumers.

**Acceptance**

- The fixed behavior
- Regression check on existing consumers of the touched code
</bug-template>

<spike-template>
**Question to answer**

The specific unknown, and why guessing is riskier than finding out.

**How to find out**

The concrete method — e.g. stand up a minimal webserver and capture real requests, run a probe against the live API, read the vendor's actual responses.

**Deliverable**

Written findings and/or a decision the downstream issues can cite — knowledge, not shipped features. (Small enabling code, like the capture harness itself, may land.)
</spike-template>

Do NOT close or modify any parent issue.

---

*Inspired by the `to-tickets` skill in [mattpocock/skills](https://github.com/mattpocock/skills); this version has diverged enough to be maintained independently.*
