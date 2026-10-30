# AGENTS.md

This file provides guidance to AI coding agents working in this repository.

## What this repo is

`skills` is a personal harness — a collection of **skills** (capability-shaped prompts) that local AI agents can use. It is not an application. There is no build step, no test suite, no linter, no package manager — do not invent commands that don't exist here.

Currently, installation is manual: clone the repo, then run the setup script to link the skills into the expected locations. In the future, this may be automated or integrated with npm or a package manager.

```sh
./setup.sh
```

It is idempotent. Run it after adding, removing, or renaming a skill.

## Skill shape

Every skill you add lives at `skills/<name>/` and must contain a `SKILL.md` file and `agents/openai.yaml` (twg* skills are CLI-installed and don't follow this shape). SKILL.md uses YAML frontmatter:

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

Four destinations, two patterns:

1. **`~/.agents/skills`** — a single parent symlink pointing at this repo's `skills/`. Tools that follow the AGENTS.md convention pick up everything under `skills/` automatically. If `~/.agents` is itself a symlink (e.g. managed by stow), setup bails so the user can decide.
2. **`~/.claude/skills/<name>`** — one symlink per skill. Claude Code discovers user-level skills by enumerating this directory, so each skill needs its own entry.
3. **`~/.config/opencode/skills/<name>`** — one symlink per skill, same shape. OpenCode enumerates this directory.
4. **`~/.codex/skills/<name>`** — one symlink per skill, same shape. Codex enumerates this directory.

`setup.sh` also reproduces `but agent setup` (see the gitbutler special case below): `scripts/refresh-gitbutler-skill.sh` generates `gitbutler-steering.md` and injects it into `~/.codex/AGENTS.md` and `~/.config/opencode/AGENTS.md`; `setup.sh` symlinks it to `~/.claude/rules/gitbutler.md`.

**TWG (Atlassian) skills** (`skills/twg*`) are gitignored, not committed. If the `twg` CLI is on PATH, `setup.sh` runs `twg skills install --yes`: twg keeps the real copies in `~/.config/twg/skills` and symlinks them into `~/.agents/skills` (i.e. this repo's `skills/`) and some per-agent dirs, and the per-skill linking then fans them out to every agent. `setup.sh` only runs twg once `~/.agents/skills` is its symlink (otherwise twg would create a real directory there and cut off the custom skills), leaves any link that already resolves to the right directory, and prunes dangling `twg*` links. Update them with `twg upgrade` + `./setup.sh`, not by hand.

`setup.sh` reports new symlinks, replaced symlinks (target moved), skipped real directories (won't clobber), and dangling symlinks (point at non-existent paths — usually leftovers from a renamed/removed skill; remove manually — except dangling `twg*` links, which it prunes).

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

**Special case — `gitbutler`:** not vendored — generated. `scripts/refresh-gitbutler-skill.sh` runs `but skill install --path skills/gitbutler` whenever the `version:` stamp in `SKILL.md` differs from `but --version`, so the skill always matches the installed CLI. Only `skills/gitbutler/agents/` is tracked; the rest is gitignored. Never edit the generated files. The script runs from `setup.sh`, a Claude Code `SessionStart` hook (`~/.claude/settings.json`), and an OpenCode plugin (`~/.config/opencode/plugins/gitbutler-skill-refresh.js`). This doesn't contradict the no-auto-update rule: the content comes from the `but` binary agents already execute, not from a remote feed. The steering text works the same way: `gitbutler-steering.md` (gitignored) = `but agent setup --print` (the defaults, versioned with the CLI) + `gitbutler-steering.extra.md` (tracked; the wizard's opt-in sections, which `--print` omits). To change which opt-ins you use, edit `gitbutler-steering.extra.md` — the next run picks it up.

### Updating a vendored skill

On need only — when the skill misbehaves, or you want a capability upstream gained. Not on a schedule (staleness here is a correctness annoyance; the update itself is the risky moment).

1. `./update-thirdparty-skills.sh <name>` — read-only: clones upstream, shows the `upstream_ref..HEAD` diff and how far the fork has diverged, and runs `skillspector scan --no-llm` on the upstream candidate. It never writes into `skills/`.
2. Read the diff yourself for injection-style changes a scanner won't flag (new shell, exfil / new URLs, "ignore previous instructions" / permission-broadening, obfuscation, trigger or `description:` changes).
3. Hand-merge the bits you want into `skills/<name>/`.
4. Bump `upstream_ref:` (to the HEAD sha the script printed) and `last_reviewed:`.
5. Run `./setup.sh`.
