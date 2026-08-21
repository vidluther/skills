# AGENTS.md

This file provides guidance to AI coding agents working in this repository.

## What this repo is

`sabu` is a personal harness — a collection of **skills** (capability-shaped prompts) that local AI agents can use. It is not an application. There is no build step, no test suite, no linter, no package manager — do not invent commands that don't exist here.

Currently, installation is manual: clone the repo, then run the setup script to link the skills into the expected locations. In the future, this may be automated or integrated with npm or a package manager.

```sh
./setup.sh
```

It is idempotent. Run it after adding, removing, or renaming a skill.

## Skill shape

Every skill lives at `skills/<name>/` and must contain a `SKILL.md` file and `agents/openai.yaml`. SKILL.md uses YAML frontmatter:

```yaml
---
name: <kebab-case-name> # must match the directory name
description: <one-line summary> # used by agents to decide when to load it
disable-model-invocation: true # optional Claude-specific auto-trigger control

# Provenance — present only on vendored (third-party) skills; see "Third-party skills".
source: <clone-able upstream repo URL>            # presence of `source:` marks a skill as vendored
source_path: <path to the skill within that repo> # optional; omit if repo root
upstream_ref: <commit/tag last reconciled against>
last_reviewed: <YYYY-MM-DD>
---
```

`agents/openai.yaml` contains Codex-facing display metadata. Use `policy.allow_implicit_invocation: false` there for skills that should only run when explicitly invoked.

Supporting files live alongside `SKILL.md` in the same directory (e.g. `marshal/triage-labels.md`, `rubber-duck/ADR-FORMAT.md`). The skill body references them by relative path; agents only read them when the skill instructs them to.

Skills cross-reference each other by name (e.g. `marshal` mentions `to-issues` and `diagnose`). Renaming or removing a skill silently breaks those references — use `rg` before doing so.

## Distribution model (what setup.sh does)

Three destinations, two patterns:

1. **`~/.agents/skills`** — a single parent symlink pointing at this repo's `skills/`. Tools that follow the AGENTS.md convention pick up everything under `skills/` automatically. If `~/.agents` is itself a symlink (e.g. managed by stow), setup bails so the user can decide.
2. **`~/.claude/skills/<name>`** — one symlink per skill. Claude Code discovers user-level skills by enumerating this directory, so each skill needs its own entry.
3. **`~/.gemini/antigravity/skills/<name>`** — one symlink per skill, same shape as Claude Code. Gemini Antigravity enumerates this directory.

`setup.sh` reports new symlinks, replaced symlinks (target moved), skipped real directories (won't clobber), and dangling symlinks (point at non-existent paths — usually leftovers from a renamed/removed skill; remove manually).

## Adding a new skill

1. Create `skills/<name>/SKILL.md` with the frontmatter above.
2. Create `skills/<name>/agents/openai.yaml` with `display_name`, `short_description`, and a `default_prompt` that mentions `$<name>`.
3. Add any supporting files in the same directory.
4. Run `./setup.sh` — it will print `linked   ~/.claude/skills/<name>`.

## Third-party (vendored) skills

Skills may be forks of public skill sets vendored into `skills/` and then adapted (currently three, all from mattpocock/skills: `diagnose`, `improve-codebase-architecture`, `rubber-duck`). When vendored, they are **ours now** — we never auto-update them.

When a vendored skill diverges so far that upstream is no longer a useful source of updates (e.g. `to-issues`), de-vendor it: remove the provenance fields from its frontmatter and credit the origin in a line at the end of the skill body instead.

**Why no auto-update:** a skill is instructions an agent *executes* while holding real tools (shell, file edits, MCP), so a vendored skill is third-party *code you run*. Auto-pulling upstream would be an unattended supply-chain channel — upstream changes the prompt, the next agent run obeys it. So upstream is a place we shop on need, not a feed we sync from. (Full rationale in the README "Security" section. Do not "helpfully" automate this away.)

A vendored skill records its origin in the flat top-level frontmatter fields above. The presence of `source:` is what marks a skill as vendored; `rg '^source:' skills/*/SKILL.md` audits them. Bespoke skills have no `source:`.

**Special case — `gitbutler`:** vendored from the `but agent setup` wizard (GitButler CLI), not a git repo, so it has no `source:` frontmatter — the wizard version-stamps `SKILL.md` itself (`version:`). Its `SKILL.md` is wizard-owned: leave it (including `name: but`) untouched so future wizard runs diff cleanly. To update, re-run `but agent setup`, diff what it writes, then copy the regenerated `~/.claude/rules/gitbutler.md` over `gitbutler-steering.md` — **not** via `update-thirdparty-skills.sh`. The steering block in `gitbutler-steering.md` is mirrored into agent instruction files by `setup.sh`.

### Updating a vendored skill

On need only — when the skill misbehaves, or you want a capability upstream gained. Not on a schedule (staleness here is a correctness annoyance; the update itself is the risky moment).

1. `./update-thirdparty-skills.sh <name>` — read-only: clones upstream, shows the `upstream_ref..HEAD` diff and how far the fork has diverged, and runs `skillspector scan --no-llm` on the upstream candidate. It never writes into `skills/`.
2. Read the diff yourself for injection-style changes a scanner won't flag (new shell, exfil / new URLs, "ignore previous instructions" / permission-broadening, obfuscation, trigger or `description:` changes).
3. Hand-merge the bits you want into `skills/<name>/`.
4. Bump `upstream_ref:` (to the HEAD sha the script printed) and `last_reviewed:`.
5. Run `./setup.sh`.
