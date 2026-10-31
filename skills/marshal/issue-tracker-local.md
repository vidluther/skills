# Issue tracker: local files

Issues live as markdown files in `issues/`, one per issue, named `NNNN-short-slug.md` with the
next free number. `issues/README.md` is a flat index: one line per issue with its number,
status, and title. There is no parent/child hierarchy.

## File shape

```markdown
# 0004 Add Needs EOB status to report-workorders

Status: open · Type: afk · Blocked by: 0002

## What
## Why
## Done when
```

- The status line holds all metadata: `Status` (open, in progress, done, wontfix), `Type`
  (`afk` / `hitl`, plus `bug` when it is one), and `Blocked by` only when something blocks it.
  Never write "none".
- The body follows the `to-issues` templates. Nothing else goes above **What**.
- When an issue is done, change its status, note any deviation at the bottom, and update the
  index line.

## When a skill says "publish to the issue tracker"

Write the next numbered file in `issues/` and add its line to `issues/README.md`.

## When a skill says "fetch the relevant ticket"

Read `issues/NNNN-*.md`, plus any issue it lists under `Blocked by`.

## Moving to a remote tracker later

Create one remote issue per open file, keep the body, move the status line into native
fields, and note the new ID at the top of `issues/README.md`. Done files don't need moving.
