---
name: log-workout
description: Log Vid's workout — interview for weights/reps per exercise, append to strength-log.csv and Workout Log, reset the day file. Use when he says "log my workout", "log today's session", or reports finishing a gym session or wants to record exercise weights.
---

# Log workout

**Read `/Users/vluther/Documents/Obsidian Vault/Areas/Health & Fitness/Health Data Pipeline.md` first** — it holds the strength-log schema (§Strength log) including the tracked-holds list, plus exclusions and context. Dashboard/reconcile/check-in belong to the `health-dashboard` skill; this skill only logs sessions.

All paths below are in the vault under `Areas/Health & Fitness/`.

## Flow

1. **Identify the session**: today's day file in `Training Week/` (`day:` frontmatter matches the weekday). Stale ticks from an earlier day → log them under that date first (see AGENTS.md).
2. **Interview, pre-filled** — one short round, not one message per exercise:
   - For each **main-block** exercise (strength days) or **loaded movement** (conditioning days), look up the most recent row for that exercise in `strength-log.csv` and propose it: "Incline DB Press — last time 4×10 @ 22.5. Same?" First time ever: ask for the numbers.
   - Always ask the **tracked holds** (pipeline doc list; currently Deep Squat Hold): "how long did you hold?" Record *achieved* time, not the prescription.
   - Vid answers with deviations only; "same" means copy the prior row. Don't nag for what he doesn't remember — leave `weight` empty with a note.
3. **Append to `strength-log.csv`** — one row per exercise: `date,session,exercise,sets,reps,weight,notes`. Weight in **kg**, `BW` for bodyweight, reps may be time (`45s`) or distance (`30m`). Extra rows for the same exercise if sets genuinely differed (top set / back-offs). Never edit past rows except to fix errors.
4. **Workout Log entry** (`Workout Log.md`, newest first): standard format — done / skipped / notes / `health-data: (pending — Apple Health reconciliation)`, or fill it directly from today's `dw_` export if it already exists (paths in pipeline doc).
5. **Reset the day file's checkboxes** so the week self-renews. Exercise lists change only when Vid or his trainer says so.
6. **Daily note pointer** — one line under `## Log` in `Daily/YYYY-MM-DD.md`.

## Rules

- Progressive-overload status is **computed** (by health-dashboard) from the CSV, never stored in it.
- Warm-up and mobility trivia (cat-camel, neck circles, wall slides) never get CSV rows.
- If Vid volunteers pain, PRs, or trainer changes, put them in `notes` (CSV and/or log entry) verbatim.
- If he says everything was done without ticking, trust him — tick nothing retroactively, just log.
