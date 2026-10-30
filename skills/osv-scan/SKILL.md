---
name: osv-scan
description: Scan a project folder for known-vulnerable dependencies with osv-scanner, triage the findings by severity and upgrade effort, and recommend a systematic remediation plan — grouped safe bumps, separate tickets for breaking upgrades, and long-term automation (Dependabot, osv-scanner in CI) — with ticket drafts for approval. Use whenever the user asks to run osv-scanner, audit or scan dependencies for vulnerabilities/CVEs, check whether a repo has vulnerable packages, triage `npm audit`/`pnpm audit`-style findings, or asks "what should we do about these vulns", even if they don't name osv-scanner.
---

# OSV Scan

Scan a folder for vulnerable dependencies and tell me what to do next. The goal isn't a wall of CVEs — it's a plan I can turn into a few well-scoped tickets, plus a fix so I don't have to do this by hand again.

Nothing is installed, created, or changed without my say-so. This skill reads, scans, and drafts.

## 1. Preflight

1. **Is osv-scanner available?** `command -v osv-scanner && osv-scanner --version`.
   If missing, stop and tell me. Don't install it — I decide where tools come from. Mention the usual sources (`brew install osv-scanner`, `go install github.com/google/osv-scanner/v2/cmd/osv-scanner@latest`, nix) so I can pick.
2. **Which folder?** Default to the current working directory. If I named a path, use that.
3. **Ask before every scan.** Even if a permission rule would auto-allow it, ask me first and wait for a yes. The scan sends package names and versions to osv.dev and deps.dev, which I may not want for a private or client repo. Show the exact command and folder:

   > Run `osv-scanner scan source -r --format json .` in `<abs path>`? It sends package names + versions to osv.dev. Alternative: offline mode (`--offline-vulnerabilities --download-offline-databases`).

   If my request already gave explicit permission for this scan ("go ahead and scan", "you have permission"), that counts. A general request to "check for vulns" does not.

## 2. Scan

Write output to a temp file, not the repo. The JSON is huge (hundreds of KB for a handful of packages), so don't read it raw.

```bash
OUT="${TMPDIR:-/tmp}/osv-$(date +%s).json"
osv-scanner scan source -r --format json <folder> > "$OUT" 2> "$OUT.err"; echo "exit=$?"
```

Interpret the exit code before anything else:

| Exit | Meaning | Do |
| --- | --- | --- |
| 0 | No known vulns | Report clean. Still do step 4 (automation check). |
| 1 | Vulns found | Continue. |
| 128 | No lockfiles/manifests found | Say so. Common causes: wrong folder, deps not locked yet (no `package-lock.json`/`pnpm-lock.yaml`/`go.sum`…). Don't treat as clean. |
| other | Error | Show the tail of `$OUT.err` and stop. |

## 3. Triage

Summarize with the bundled script. It's TypeScript with no dependencies, and Node 23.6+ runs it directly:

```bash
node <skill-dir>/scripts/summarize.ts "$OUT"          # markdown table
node <skill-dir>/scripts/summarize.ts "$OUT" --json   # rows, if you need to compute groups
```

Each row is one vulnerable package. It lists severity (from the highest CVSS score, falling back to the GitHub advisory label), the lowest version that clears every fixable advisory, the bump type needed (`patch`/`minor`/`major`; pre-1.0 minor bumps count as major), whether it's a direct dependency (heuristic: named in a sibling manifest), and any advisories with no fix.

Then gather the context the plan depends on. These are all read-only:

- **Package manager**: which lockfile it is (`pnpm-lock.yaml` → pnpm, etc.). Fix commands must use that tool.
- **Transitive parents**: for each non-direct package, find what pulls it in (`pnpm why <pkg>`, `npm ls <pkg>`, `go mod why -m <mod>`, `cargo tree -i <crate>`). Bumping the parent usually clears a cluster of transitive vulns at once, which is a better ticket than "bump qs".
- **Existing automation**: `.github/dependabot.yml`, `renovate.json`/`.github/renovate.json5`, any workflow running osv-scanner or `audit`.
- **Fixes already waiting**: if `gh` works, list open dependency PRs (`gh pr list --author app/dependabot --state open` and the Renovate equivalent). A vuln with an open PR is "merge PR #N", not a new ticket.
- **Where tickets go**: look for the repo's tracker in its docs (`AGENTS.md`, `docs/agents/issue-tracker.md`). Global defaults in my instructions don't count. One project might use Jira and another GitHub Issues, so if the repo doesn't say, ask in step 6 rather than guessing.

## 4. Plan

Turn the rows into work units. The aim is the fewest tickets that each make sense as one PR.

1. **Merge what's already open.** Existing Dependabot/Renovate PRs that fix listed vulns come first.
2. **One grouped "safe bumps" ticket.** Put every `patch`/`minor` fix in it, including transitive ones that a parent's patch/minor clears. One PR, low risk, and it usually clears most of the count. Prioritize it at the highest severity it contains.
3. **One ticket per Critical/High major bump.** Major upgrades need code changes and their own testing, so each gets its own ticket. Link the changelog/migration guide if you can find it.
4. **One grouped ticket for Medium/Low majors.** Batch them. They're backlog, not fire drills.
5. **One ticket for no-fix advisories.** Options are replace the package, accept the risk with an `osv-scanner.toml` `[[IgnoredVulns]]` entry (with `reason` and `ignoreUntil`), or mitigate in code. Don't silently ignore anything.
6. **Long-term: stop doing this by hand.** One ticket:
   - **No Dependabot** → add `.github/dependabot.yml` for each ecosystem/directory found. Use a `groups:` block so minor+patch updates arrive as one weekly PR (that mirrors step 2 automatically), and turn on Dependabot security updates in repo settings.
   - **Dependabot exists but these vulns slipped through** → diagnose why. Check whether the ecosystem or directory is covered, whether `open-pull-requests-limit` is hit, whether `ignore:` entries hide it, and whether security updates/alerts are on (`gh api repos/{owner}/{repo}/vulnerability-alerts`; 204 = on).
   - **Add osv-scanner to CI** (`google/osv-scanner-action`) so new vulns fail a PR instead of waiting for the next manual scan. If the repo has CI rules about what runs on PRs, respect them.

Severity buckets (CVSS v3): Critical ≥ 9.0, High 7.0–8.9, Medium 4.0–6.9, Low < 4.0. Treat "unknown" severity like Medium until someone reads the advisory.

## 5. Report

Keep it scannable. I want the shape of the problem and the next action, not every CVE. Use this structure:

```
**<N> vulnerable packages, <M> advisories** — Critical X · High Y · Medium Z · Low W
Scanned: <folder> (<lockfiles>)

**Next step:** <the single most valuable action, e.g. "merge Dependabot PR #41, then the safe-bumps ticket clears 7 of 10">

**Plan**
1. <ticket title> — <severity> — <packages> — <one-line why it's grouped this way>
2. …

**Automation:** <Dependabot/CI status in one line + what the long-term ticket fixes>

<collapsed or trailing: the summarize.ts table>
```

## 6. Tickets: ask before drafting

**Never create a ticket, branch, or PR, and never edit dependency files, until I approve.**

End the report with a short question, and don't draft any tickets yet:

1. **Which tracker?** Skip this if the repo's docs named one in step 3; otherwise ask (Jira project, GitHub Issues, other).
2. **Use `to-issues`?** Check whether a `to-issues` skill is in your available skills. If it is, ask whether I want it to turn the plan into issues. It breaks a plan into tracer-bullet issues that follow the repo's tracker conventions, so it usually beats hand-drafting here. If it isn't available, don't mention it.

Example ending:

> Where should these go — Jira (which project?) or GitHub Issues? And want me to hand this plan to `to-issues` to create them, or should I draft them here?

Then act on my answer:

- **`to-issues`** → invoke it with the plan from step 4 as input: the work units, severities, packages, fix commands and scan evidence. It handles drafting, approval and creation.
- **Draft here** → write the drafts using the format below. Wait for approval, then create them in the tracker I named and link them to each other.

### Draft format

If my instructions define a ticket format, use it. Otherwise use this shape:

- **Title** states the goal, not the fix: "Clear high-severity axios advisories", not "Bump axios to 1.x". Repo-scoped work gets a `[repo-name]` prefix.
- **Context**: one paragraph covering what's vulnerable and where (lockfile path).
- **Evidence**: the relevant rows from the summarize table and the advisory IDs (CVE preferred, GHSA otherwise), plus the scan command and date.
- **Work**: bullets with exact commands for the repo's package manager (e.g. `pnpm update lodash@^4.18.0`, or bump the parent `express@^4.20.0`). Use overrides/resolutions only as a last resort, and say so when you do.
- **Testing**: bullets. Re-run `osv-scanner scan source -r .` and expect these IDs gone; run the repo's build/test/lint commands.
- **Related**: links to the sibling tickets from this scan.

## Re-running after fixes

If I come back after applying fixes, re-scan (asking again) and diff against the previous summary: what cleared, what's left, and anything new.
