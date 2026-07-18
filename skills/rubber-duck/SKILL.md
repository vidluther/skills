---
name: rubber-duck
description: Interview the user relentlessly about a plan or design, one question at a time, until reaching shared understanding — resolving each branch of the decision tree. When the project documents its domain (CONTEXT.md, ADRs), challenge the plan against that language and capture decisions inline. Use when the user wants to stress-test a plan or an issue, asks your opinion on a plan or design, or mentions "rubber-duck" / "rubberducking".
source: https://github.com/mattpocock/skills
source_path: skills/productivity/grilling
upstream_ref: 9603c1cc8118d08bc1b3bf34cf714f62178dea3b
last_reviewed: 2026-07-17
---

<what-to-do>

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the decision tree, resolving dependencies between decisions one-by-one.

Ask one question at a time, and wait for my answer before moving to the next one. This is the whole point: ten questions fired at once is a form, not an interview. For each question, give your recommended answer and the reasoning behind it — but treat it as a proposal, not a verdict. Wait for me to confirm or redirect before walking down that branch. The recommendation exists to move us forward, not to answer the question for me.

If a *fact* can be found by exploring the codebase, look it up rather than asking me. The *decisions*, though, are mine — put each one to me and wait for my answer.

Do not act on the plan until I confirm we have reached a shared understanding.

Once I confirm, offer to save the final plan as `docs/plans/<model>-<topic>.md` — `<model>` is a short slug for the model you are running on (fable, opus, kimi, gpt5, …), `<topic>` a kebab-case slug for the work (ask me if it isn't obvious). I may run this same interview on other models; `/reconcile-plans` merges the saved plans into a final one.

</what-to-do>

<supporting-info>

Everything above is the whole skill for a quick stress-test. The rest engages when the project documents its domain — when you find the docs below, or when I ask you to capture what we decide.

## Domain awareness

During codebase exploration, also look for existing documentation:

### File structure

Most repos have a single context:

```
/
├── CONTEXT.md
├── docs/
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

If a `CONTEXT-MAP.md` exists at the root, the repo has multiple contexts. The map points to where each one lives:

```
/
├── CONTEXT-MAP.md
├── docs/
│   └── adr/                          ← system-wide decisions
├── src/
│   ├── ordering/
│   │   ├── CONTEXT.md
│   │   └── docs/adr/                 ← context-specific decisions
│   └── billing/
│       ├── CONTEXT.md
│       └── docs/adr/
```

Create files lazily — empty scaffolding just rots, leaving the next person to wonder whether it was ever filled in. If domain docs already exist, update them inline as decisions resolve. If none exist, stay in the plain interview by default; when the first term or decision is worth keeping, offer to start a `CONTEXT.md` or ADR rather than creating one silently.

## During the session

### Challenge against the glossary

When the user uses a term that conflicts with the existing language in `CONTEXT.md`, call it out immediately. "Your glossary defines 'cancellation' as X, but you seem to mean Y — which is it?"

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. "You're saying 'account' — do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios

When domain relationships are being discussed, stress-test them with specific scenarios. Invent scenarios that probe edge cases and force the user to be precise about the boundaries between concepts.

### Cross-reference with code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it: "Your code cancels entire Orders, but you just said partial cancellation is possible — which is right?" Resolve it before moving on: ask which is correct, then fix whatever was wrong — correct the doc, adjust the plan, or note that the code itself needs to change.

### Update CONTEXT.md inline

When a term is resolved, update `CONTEXT.md` right there. Don't batch these up — capture them as they happen. Use the format in [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md).

Don't couple `CONTEXT.md` to implementation details. Only include terms that are meaningful to domain experts.

### Offer ADRs sparingly

Only offer an ADR when the decision is hard to reverse, surprising without context, and the result of a real trade-off. If any of the three is missing, skip it. See [ADR-FORMAT.md](./ADR-FORMAT.md) for the full test and what qualifies.

</supporting-info>
