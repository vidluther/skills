# ISA Format

An **Ideal State Artifact** is one document per initiative: the closest written representation of what "done" looks like. Code is judged against it, and a bad implementation can be thrown away and rebuilt against the same ISA. One ISA per **unit of intent** — never one per issue (issues cite the ISA's criteria instead). `marshal`'s `isa.md` template mirrors this shape; keep them in sync.

## Structure

```markdown
# <Initiative> — ISA

Parent: <link to parent ISA, or omit>

## Ideal State

<Prose. What it's like when this is done, in the user's words — the experience, not the implementation. A paragraph to a few pages.>

## Constraints

- <what this must not do, or must respect>

## Decisions

- YYYY-MM-DD — <what changed in the ideal state or constraints> — <why>

## Ideal State Criteria

- **ISC-1** — <criterion> — eval: <rung>: <how it's checked>
- **ISC-2** — …

## Status

- ISC-1 — untested
- ISC-2 — untested
```

## Writing good ISCs

- **Atomic** — one checkable thing. "Books in ≤3 taps and shows the roster" is two ISCs.
- **A state, not a task** — "A regular can book Thursday's class without logging in", not "Build the booking flow". Tasks belong in issues.
- **Binary** — a reader can say pass or fail without arguing.
- **Numbered for life** — never renumber. A dropped ISC stays, struck through, with a Decisions entry; new ones take the next number. Issues cite these IDs.

## Picking the eval rung

Cheapest rung that can actually judge the criterion:

1. **assert** — a plain check on output or data ("no meal contains peanuts").
2. **test** — an automated test in the project's framework (unit, integration, e2e).
3. **question set** — a fixed list of yes/no questions a fast model or person answers against the output ("would a 7-year-old eat this?").
4. **judge** — a stronger model or a human scores against a rubric. For subjective criteria ("feels watchful", "menu has variety").

If no rung can judge it, the ISC isn't atomic or concrete enough — sharpen it.

Make the method runnable where you can (`eval: test: pnpm vitest run -t "ISC-1"`), and name tests after the ISC they prove — `isa-check` finds evidence by ISC ID.

## Decisions log

Append-only, dated, newest last. Write an entry whenever the ideal state, a constraint, or an ISC changes — including changes discovered while building. The change goes here first, then into the sections above. Don't bury a change of mind in code.

## Status

One line per ISC: `pass`, `fail`, or `untested`, with the date and commit it was checked at (`isa-check` writes these). It's a snapshot, not a log — overwrite freely.
