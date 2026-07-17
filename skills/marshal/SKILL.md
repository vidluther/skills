---
name: marshal
description: Sets up project rails for human + AI collaboration. Walks through five sections — CLAUDE.md/AGENTS.md coherence, issue tracker + triage labels, domain doc layout, code-style conventions, and version-control conventions — recording the result so the engineering skills (`to-issues`, `to-prd`, `diagnose`, `tdd`, `improve-codebase-architecture`, `zoom-out`) and any humans working alongside agents share the same baseline. Run on any new or existing repo before starting agent-driven work, or when those skills appear to be missing context.
disable-model-invocation: true
---

# Marshal

Marshal lays the rails. It walks through the conventions an AI agent (and any humans working alongside one) needs to know to operate coherently inside a repo: where issues live, how they move through triage, where domain docs are kept, what code style is in force, and how work flows through git. The result is recorded in `CLAUDE.md` (or `AGENTS.md`) and `docs/agents/`, so every subsequent engineering skill reads the same playbook.

This is a prompt-driven skill, not a deterministic script. Explore the repo, present what you found, confirm with the user, then write. Each of the five sections is independent — re-running marshal later only revisits the sections that changed.

## Process overview

1. **Explore** the repo's starting state (read whatever exists; don't assume).
2. Walk the user through five sections **one at a time** — explain, ask, confirm, write. Don't dump the whole walkthrough up front.
3. After all five sections, summarise what was recorded and where.

Each section follows the same shape:
- **Explainer** — what this is, why agents need it, what changes if the user picks differently. Assume the user does not know the term.
- **Detect** — read the repo (and where applicable, the user's `~/.claude/CLAUDE.md` for global preferences) to propose a default.
- **Decide** — present the choice, accept overrides, surface conflicts.
- **Write** — update `CLAUDE.md` and/or `docs/agents/` files in place.

## 1. Explore

Read whatever exists. Don't assume.

- `git remote -v` and `.git/config` — is this a GitHub repo? Which one?
- `CLAUDE.md` and `AGENTS.md` at the repo root — does either exist? If both, are they identical (a symlink), or have they drifted apart? Is there already an `## Agent skills` section?
- `CONTEXT.md` and `CONTEXT-MAP.md` at the repo root.
- `docs/adr/` and any `src/*/docs/adr/` directories.
- `docs/agents/` — does marshal's prior output already exist?
- `package.json`, lockfiles (`pnpm-lock.yaml`, `package-lock.json`, `yarn.lock`, `bun.lockb`), `.eslintrc*`, `oxlint.json`, `vitest.config.*`, `tsconfig.json`, `pyproject.toml`, etc.
- `.gitbutler/` directory; `.husky/` or `lefthook.yml`; recent commit messages (`git log --oneline -20`) to spot conventional-commits or other patterns.
- `~/.claude/CLAUDE.md` — the user's global preferences. Used in sections 4 and 5 to flag conflicts when project reality diverges.

## 2. Walk through the sections

Present a short summary of what you found, then move into the sections one at a time.

---

### Section 1 — Repo coherence

> **Explainer:** Claude Code reads `CLAUDE.md`; some other AI tools read `AGENTS.md`. If a repo has both, they need to stay in sync — otherwise humans and agents end up working from different rules. The cleanest setup is a single source of truth (one file, with the other symlinked to it). The `## Agent skills` block written by marshal lives in whichever file is canonical.

Detect:
- If only one of `CLAUDE.md` / `AGENTS.md` exists — that's the canonical file. Done.
- If both exist and one is a symlink to the other — already coherent. Note which is canonical.
- If both exist as separate files — flag the drift. Show the user a diff and offer to:
  - Symlink one to the other (user picks which is canonical).
  - Merge them manually (marshal stops here for this section; user resolves before re-running).
- If neither exists — ask the user which to create (`CLAUDE.md` is the Claude Code default; pick `AGENTS.md` only if other AI tools are the primary readers).

Never silently overwrite or merge. Drift between the two files often encodes intentional differences; surface, don't fix.

The `## Agent skills` block goes in the canonical file.

---

### Section 2 — Where work happens

> **Explainer:** The "issue tracker" is where issues live for this repo. Skills like `to-issues` and `to-prd` read from and write to it — they need to know whether to call `gh issue create` or follow some other workflow you describe. Pick the place you actually track work for this repo.

Default posture: these skills were designed for GitHub. If a `git remote` points at GitHub, propose that. Otherwise (or if the user prefers), offer:

- **GitHub** — issues live in the repo's GitHub Issues (uses the `gh` CLI).
- **Other** (GitLab, Jira, Linear, etc.) — ask the user to describe the workflow in one paragraph; the skill will record it as freeform prose in `docs/agents/issue-tracker.md`.

#### Triage label vocabulary

> **Explainer:** When an incoming issue is triaged, it gets tagged with **state** labels (`needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`) so anyone — human or agent — can tell at a glance what's actionable. Issues created via `to-issues`/`to-prd` also get a **provenance** label (`new`) so agent-created issues are distinguishable from human-opened ones. To do this, the actual label strings in your tracker need to match what the skills expect. If your repo already uses different vocabulary (e.g. `untriaged` instead of `new`), record the mapping here so the skill applies the right ones instead of creating duplicates.

Canonical vocabulary:

**State labels** (mutually exclusive; one per triaged issue):
- `needs-info` — waiting on reporter for more information
- `ready-for-agent` — fully specified, AFK-ready (an agent can pick it up with no human context)
- `ready-for-human` — needs human implementation (judgment calls, external access, design decisions, manual testing)
- `wontfix` — will not be actioned

An issue with **no state label** is in the inbox — it hasn't been triaged yet.

**Provenance label** (optional):
- `new` — created via `to-issues`/`to-prd` (agent-flow). Issues opened directly by humans carry no provenance label.

**Category labels** (mutually exclusive):
- `bug` — something is broken
- `enhancement` — new feature or improvement

#### Detect existing labels

For GitHub trackers, run `gh label list --json name,description,color` to enumerate existing labels. Then:

1. **Map canonical → repo labels.** For each canonical label, ask the user whether the repo already uses a different string. Default: each role's string equals its name.
2. **Create missing canonical labels.** If any of the 7 canonical labels don't physically exist in the tracker, offer to create them via `gh label create <name> --description "<meaning>" --color <hex>`. Otherwise `gh issue edit --add-label` will fail at runtime when a skill tries to apply them. Sensible defaults: `needs-info` orange, `ready-for-agent` green, `ready-for-human` blue, `wontfix` grey, `new` light blue, `bug` red, `enhancement` purple.
3. **Record non-canonical labels.** Everything else (`security`, `p0`, `area:auth`, `regression`, etc.) gets recorded in `docs/agents/triage-labels.md` under "Other labels in this repo". Skills surface these in agent briefs so implementing agents see the full context (an issue with `ready-for-agent + security` should be handled very differently from a routine `ready-for-agent + bug`).

For non-GitHub trackers, ask the user to describe the equivalent vocabulary as freeform prose.

---

### Section 3 — What things mean

> **Explainer:** Some skills (`improve-codebase-architecture`, `diagnose`, `tdd`) read a `CONTEXT.md` file to learn the project's domain language, and `docs/adr/` for past architectural decisions. They need to know whether the repo has one global context or multiple (e.g. a monorepo with separate frontend/backend contexts) so they look in the right place. Marshal also pre-creates the `.out-of-scope/` directory used to record rejected feature requests with reasoning.

Confirm the layout:

- **Single-context** — one `CONTEXT.md` + `docs/adr/` at the repo root. Most repos are this.
- **Multi-context** — `CONTEXT-MAP.md` at the root pointing to per-context `CONTEXT.md` files (typically a monorepo).

Marshal does not fill in `CONTEXT.md` content — that's `rubber-duck`'s job, and it happens lazily as terms get resolved during real work. Marshal only records where these files live so the consumer skills know where to look.

Offer to create empty `docs/adr/` and `.out-of-scope/` directories if they don't exist (with a `.gitkeep` so they survive git).

---

### Section 4 — How code is written

> **Explainer:** Agents writing code for this repo need to follow the project's existing conventions — linter, formatter, test framework, package manager. Otherwise their output won't match house style and CI will reject it. Marshal records what the project uses so every agent reads the same answer.

#### Detect

From the repo:
- **Package manager**: lockfile presence determines this. `pnpm-lock.yaml` → pnpm. `yarn.lock` → yarn. `bun.lockb` → bun. `package-lock.json` → npm. Multiple lockfiles → flag the inconsistency.
- **Linter**: `oxlint.json` or `oxlint` in `package.json` scripts → oxlint. `.eslintrc*` or `eslint` in scripts → eslint. Both → flag.
- **Formatter**: `oxfmt` config or script → oxfmt. `.prettierrc*` or `prettier` script → prettier. Look at `package.json` `scripts.format` for the active one.
- **Test framework**: `vitest.config.*` or `vitest` script → vitest. `jest.config.*` or `jest` script → jest. Other (mocha, ava, node:test): record what's there.
- **Language**: `tsconfig.json` → TypeScript. `pyproject.toml` → Python (record uv/poetry/pip from there). `Cargo.toml` → Rust. Etc. Detect the primary language(s).

From `~/.claude/CLAUDE.md`: read it as plain text and note the user's global preferences (the user's CLAUDE.md typically has a "Code Style" or "Tool Preferences" section).

#### Flag conflicts

If repo reality and global prefs diverge, surface explicitly:

> "This repo uses `eslint` + `jest` + `npm`. Your global prefs are `oxlint` + `vitest` + `pnpm`. Marshal will record the repo's current state — your global rule already says 'follow whatever tooling is already configured, don't introduce new tools without asking.' If you want to migrate, that's a separate task (`/migrate-oxlint` for the linter side)."

Never auto-migrate. Marshal only records.

#### Write

Update or create a `## Code Style` section in `CLAUDE.md` listing:
- Primary language(s)
- Linter, formatter, test framework, package manager (the actual ones, not your global preferences)
- Any other conventions worth noting (TypeScript strictness level, import style, etc.) — ask the user

If the section already exists, edit it in place; don't append a duplicate. Preserve any user-authored prose around it.

---

### Section 5 — How work moves

> **Explainer:** Agents need to know how this project handles version control: bare git, GitButler (`but` CLI), commit message conventions, branch model, whether they should propose merges or stop short. Recorded so every agent picks up the same workflow.

#### Detect

From the repo:
- **Tooling**: `.gitbutler/` → GitButler is in use. `.husky/` or `lefthook.yml` → pre-commit hooks. CI configs (`.github/workflows/`, `.gitlab-ci.yml`) — note whether tests/lint run on every PR.
- **Commit style**: `git log --oneline -20` — look for conventional-commits prefixes (`feat:`, `fix:`), present-tense verbs, ticket numbers, etc. Note the dominant style.
- **Branch model**: `git branch --remotes` and a recent merge commit — look for `main` vs `master`, evidence of trunk-based vs gitflow, etc.

From `~/.claude/CLAUDE.md`: note any version-control preferences (e.g. the user's global CLAUDE.md may say "use `but` not `git`" or "do not commit unless explicitly asked").

#### Flag conflicts

Same pattern as Section 4. If the repo uses bare git but your global prefs say `but`, surface that as information, not as a thing to fix. Marshal records the repo reality.

#### Write

Update or create a `## Version Control` section in `CLAUDE.md`. Capture:
- Git tooling (bare git or GitButler).
- Commit message conventions (with examples from `git log` if a clear pattern exists).
- Whether agents should commit/push/open PRs proactively, or only when asked.
- Anything specific to this repo (e.g. "always run tests before pushing", "never force-push to main").

If the user's global `~/.claude/CLAUDE.md` already states a strong preference (e.g. "do not commit unless explicitly asked"), don't duplicate it here unless the repo overrides it.

---

## 3. Confirm and edit

Before writing anything to disk, show the user a draft of:

- The `## Agent skills` block to add to the canonical `CLAUDE.md` / `AGENTS.md`.
- The `## Code Style` section (if section 4 produced one).
- The `## Version Control` section (if section 5 produced one).
- The contents of `docs/agents/issue-tracker.md`, `docs/agents/triage-labels.md`, `docs/agents/domain.md`.

Let them edit before writing.

## 4. Write

**Pick the canonical file from Section 1's outcome:**

- If `CLAUDE.md` is canonical, edit it.
- If `AGENTS.md` is canonical, edit it.
- If they're symlinked, edit the source.

If an `## Agent skills` / `## Code Style` / `## Version Control` block already exists, update its contents in-place rather than appending a duplicate. Don't overwrite user edits to the surrounding sections.

The `## Agent skills` block:

```markdown
## Agent skills

### Issue tracker

[one-line summary of where issues are tracked]. See `docs/agents/issue-tracker.md`.

### Triage labels

[one-line summary of the label vocabulary]. See `docs/agents/triage-labels.md`.

### Domain docs

[one-line summary of layout — "single-context" or "multi-context"]. See `docs/agents/domain.md`.
```

Then write the three docs files using the seed templates in this skill folder as a starting point:

- [issue-tracker-github.md](./issue-tracker-github.md) — GitHub issue tracker
- [triage-labels.md](./triage-labels.md) — label mapping (state + provenance + non-canonical)
- [domain.md](./domain.md) — domain doc consumer rules + layout

For "other" issue trackers, write `docs/agents/issue-tracker.md` from scratch using the user's description.

## 5. Done

Tell the user:
- Which sections were recorded and where.
- That they can edit `docs/agents/*.md` and `CLAUDE.md` directly later — re-running marshal is only necessary if they want to change a section's underlying decisions.
- Pointers to follow-up skills if relevant (e.g. `/update-config` for hooks, `/migrate-oxlint` if a linter conflict was flagged, `/rubber-duck` to start filling `CONTEXT.md`).
