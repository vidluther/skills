---
name: zoom-out
description: Tell the agent to zoom out and give broader context or a higher-level perspective. Use when you're unfamiliar with a section of code or need to understand how it fits into the bigger picture.
disable-model-invocation: true
---

I don't know this area of code well. Go up a layer of abstraction and give me a map, using the project's domain glossary vocabulary (`CONTEXT.md`, if it exists).

Shape the map as:

1. **Purpose** — what this area does, in 1–2 sentences of domain language.
2. **Modules** — the relevant modules, one line each on its responsibility, with a file reference.
3. **Callers and entry points** — who calls into this area and from where (routes, jobs, CLI, other modules).
4. **Dependencies** — what this area calls out to.
5. **Where to start reading** — the 2–3 files I should open first, in order.

Only include what you verified in the code; mark anything inferred.
