# Sabu

Sabu is the harness — a collection of skills, rules, and conventions I use with AI coding agents (primarily Claude Code) so they understand how I work and what I expect.

The name is from Chacha Chaudhary, the Indian comic series. Chacha is the brain ("Chacha Chaudhary ka dimaag computer se bhi tez chalta hai" — Chacha's brain works faster than a computer); Sabu is the loyal, super-strong sidekick from Jupiter who handles the heavy lifting once Chacha decides what to do. That's the model: I'm the thinker, Sabu is the agent that executes.

## What's in here

- **`skills/`** — a collection of skills (capability-shaped prompts) the agent can pick up and run. Each one is a SKILL.md plus optional supporting files. The skills live by themselves so they can be invoked individually (`/marshal`, `/tdd`, etc.) and read each other for cross-reference.

The skills currently cover, roughly:

- **Project setup** — `marshal` (lays the rails: CLAUDE.md/AGENTS.md coherence, issue tracker, triage labels, domain doc layout, code style, version control conventions).
- **Issue workflow** — `to-issues` (break a plan into tickets), `to-prd` (turn a conversation into a PRD).
- **Implementation discipline** — `tdd` (red-green-refactor), `diagnose` (disciplined debugging loop), `improve-codebase-architecture` (find deepening opportunities).
- **Design / collaboration** — `rubber-duck` (interview the user about a plan, challenging it against the project's domain language and capturing decisions when the project documents them), `reconcile-plans` (the follow-up to `rubber-duck`: reconcile multiple plans for the same work — produced by different models or sessions — into one, surfacing where they agree, where they diverge, and the catches only one model noticed, optionally convening a lens-based review council), `zoom-out` (step back from current work).
- **Stack-specific helpers** — `migrate-oxlint`.

## Getting started

```sh
git clone git@github.com:vidluther/sabu.git ~/work/personal/sabu
cd ~/work/personal/sabu
./setup.sh
```

`setup.sh` symlinks each `skills/<name>/` into `~/.claude/skills/<name>` (the location Claude Code reads user-level skills from), so the skills become invokable via `/<name>` in any session. Idempotent — safe to re-run after adding skills.

## Provenance

Most of the skills are forks or evolutions of public sets — Matt Pocock's skill collection and others — adapted to my workflow. Some are bespoke. The `marshal` skill (and its state/provenance label model) was rewritten from scratch in May 2026 as part of a redesign aimed at making the harness work for any new or existing repo.

Vendored third-party skills record where they came from in their `SKILL.md` frontmatter: `source:` (upstream repo), `source_path:`, `upstream_ref:` (the commit last reconciled against), and `last_reviewed:`. The presence of `source:` is what marks a skill as third-party — `rg '^source:' skills/*/SKILL.md` lists them (currently six, all tracing back to mattpocock/skills). These are forks, not mirrors: I adapt them, so upstream is somewhere I shop for improvements on need, not a feed I sync from. To review what changed upstream before pulling anything in, run `./update-thirdparty-skills.sh <name>` — it's read-only (shows the upstream diff and a Skillspector scan; never edits `skills/`).

## Security 

I highly recommend you view the skills here, and elsewhere, before you decide to start using them yourself. Take a look at [Skillspector](https://github.com/nvidia/skillspector) and see if the skills you have do anything dangerous, and decide if you want to risk it or not.

This matters more than it looks. A skill is not documentation — it's instructions an agent *executes* while holding real tools (shell, file edits, MCP). A third-party skill is therefore code you run. That's why vendored skills here are **never auto-updated**: auto-pulling upstream would be an unattended supply-chain channel (upstream changes the prompt, your next agent run obeys it). Updates are deliberate and reviewed — `./update-thirdparty-skills.sh <name>` shows the upstream diff and runs `skillspector scan --no-llm`, you read it for injection-style changes a scanner can't catch, then you hand-merge. Don't automate that gate away.

