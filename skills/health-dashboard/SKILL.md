---
name: health-dashboard
description: Regenerate Vid's Apple Health dashboard, reconcile workouts, or produce his nightly trainer check-in from Health Auto Export data. Use when he says "update the health dashboard", "reconcile health data", "trainer check-in", or asks about his weight/body-fat/sleep/blood-pressure/training trends.
---

# Health dashboard

**Read `/Users/vluther/Documents/Obsidian Vault/Areas/Health & Fitness/Health Data Pipeline.md` first.** It is the source of truth for data paths, exclusions, personal context and analysis rules, and it is maintained alongside the dashboard. This file only covers how to run things.

## Outputs (all in the vault, `Areas/Health & Fitness/`)

- `Health Dashboard.md` — windows **7 / 30 / 90 / lifetime**. **Dashboard style, per Vid (2026-08-06): tables, compact charts, one-line takeaways — no narrative paragraphs.** Analysis and caveats live in chat when he asks, or in the pipeline doc. Unicode sparklines/bars, no charting plugin. Sections: freshness line → At a glance (4-window table) → Last 7 days → Needs attention (numbered one-liners) → 30d weekly table → 90d table+sparklines → Lifetime (phase/yearly/PR/BP tables) → Do next.
  - **Freshness header** (two lines under the title, refresh every regeneration + mirror to Notion; keep them clean — caveats go in the pipeline doc, not here):
    ```
    Updated at: **<Month D, YYYY hh:mm:ss> IST**
    Sourced from export generated on: **<Month D, YYYY hh:mm:ss> IST** · history export: **<Month D, YYYY hh:mm:ss> IST**
    ```
    Source time = mtime (`stat -f '%Sm'`) of the `dm_`/`dw_` files at read time. They regenerate hourly and have shipped broken (2026-08-06: 13:59 metrics had 295 steps vs ~2,900 real; 12:49+ workout files lost HR arrays) — **sanity-check steps/energy totals against an earlier read before trusting a fresh generation**; if degraded, compute from the validated snapshot and stamp the generation each metric actually came from. Also set frontmatter `updated:`. Note when windows end on a partial day.
- `Workout Log.md` — one entry per session; `health-data:` line carries duration, energy, avg/max HR.
- `Trainer Check-in.md` — nightly block in the trainer's format; fill Sleep/Recovery/Steps/Training from data, **leave Energy and Stress for Vid**, and say plainly when food wasn't logged rather than guessing.

## Scripts

In `scripts/`, all standalone python3 (stdlib only). They read from the iCloud paths in the pipeline doc and print to stdout — nothing writes to the vault, so they're safe to run for verification.

| Script | Purpose |
|---|---|
| `windows.py` | The 7/30/90/lifetime comparison table |
| `week.py` | 7-day window vs prior week, HR zones, logging gaps |
| `build90.py` | 90-day weekly rollups + training bars |
| `analyze_all.py` | Full-history profile: yearly/quarterly arcs, coverage, workout types |
| `rhr_zones.py` | Daily resting-HR detail + HR zones at max 167 |
| `routes.py` | Cluster GPX routes by location, compare pace across repeats |
| `visual_dash.py` | Sparklines and bar charts |

Paths are hardcoded to the scratchpad where exports were unzipped — **update the path constants** to wherever the current export lives before running.

## Cautions

- Manual exports need **"Summarize data" ON** or they're 36 MB/day and time out.
- Apply the §2 exclusions from the pipeline doc before computing anything.
- Don't report week-over-week changes in resting HR or HRV as trends (daily spread exceeds them).
- Lean-mass moves following rapid weight change are usually water — bioimpedance measures hydration.
- Health findings are pattern-reading, not medical advice. Point Vid at his doctor for anything clinical, especially blood pressure.
