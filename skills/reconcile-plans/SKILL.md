---
name: reconcile-plans
description: Reconcile multiple plans for the same piece of work — written by different models or sessions (e.g. rubber-duck runs in Fable, Opus, Kimi, GPT) — into one final plan, finding where they agree and diverge, optionally convening a council of lens-based reviewers to judge them. Use when the user wants to compare, reconcile, or merge multiple plans, asks for a council, verdict, or second opinion across plans, mentions plan files like <model>-<topic>.md, or says they ran the same planning exercise in multiple sessions — even if they don't use the word "reconcile".
---

# Reconcile Plans

Reconcile several independently-produced plans for the same work into one trustworthy picture: what every model agreed on (adopt with confidence), where they diverge (the real decisions), and what only one of them noticed (the catches worth stealing).

This is the sequential next step after `rubber-duck`: each rubber-duck session (or any other model's planning session) saves its plan as `docs/plans/<model>-<topic>.md`, and this skill compares all plans sharing a `<topic>`.

## 1. Assemble the roster

Collect the plans:

- Given a topic, glob `docs/plans/*-<topic>.md`.
- Accept explicit file paths or pasted plans for anything outside the convention.

Read every plan in full. Then confirm the roster with the user — one line per plan: file → model → one-sentence gist. Two plans is enough to run; if only one plan exists, say so and stop (there is nothing to reconcile — offer `rubber-duck` instead).

## 2. Extract the decision points

A plan is a walk through a decision tree. Before comparing prose, extract the decisions: for each plan, list the decision points it addresses and the position it takes (with its reasoning, compressed to a sentence). Align them across plans so the same decision is one row, even when plans name it differently or address it in different order.

Decision points one plan addresses and another silently skips are data, not noise — a skipped decision is a position too ("didn't consider it").

## 3. Convergence analysis

Sort every decision point into one of four buckets:

- **Settled** — all plans agree. Adopt with confidence; agreement across models is the strongest signal this process produces. But settled means "cheap to stop debating", not "proven" — the models may share training-data biases, which is exactly what the blind-spots pass below exists to catch.
- **Majority** — most agree, one dissents. Do not dismiss the outlier by count: read its reasoning. An outlier with a load-bearing argument gets promoted to Divergent; an outlier with none gets noted and closed.
- **Divergent** — genuine disagreement. These are the real decisions. For each, lay out the positions, the trade-off actually at stake, and your recommendation with reasoning.
- **Unique contributions** — a risk, edge case, or idea only one plan raised. A plan can lose every divergence and still contribute the catch that saves the project. Harvest these regardless of which plan "wins".

Also record **blind spots**: decisions or risks *no* plan addressed. Unanimous silence is not safety — the models may share training-data biases. Name what you'd expect a plan for this work to cover that none did.

## 4. Council (on request, or when divergence is heavy)

Default to the inline analysis above. Convene a council when the user asks for one, or offer it when the Divergent bucket dominates — a second layer of independent judgment is worth its cost exactly when the plans disagree most.

The council is parallel subagents, each judging **all plans through one lens** (one agent per lens, via the Agent tool):

- **Correctness / feasibility** — does each plan survive contact with the actual codebase? This judge explores the repo and checks the plans' claims against it.
- **Simplicity / YAGNI** — which plan delivers the outcome with the least machinery? What in each plan is speculative?
- **Risk / failure modes** — how does each plan fail? Migration hazards, rollback stories, blast radius.
- **Completeness** — what did each plan miss, and what did all of them miss?

**Anonymize the plans before judging.** Present them to each judge as Plan A, Plan B, Plan C — never by model name. Judges knowing "this one is GPT" or "this one is Fable" invites brand bias; the arguments must win, not the logo. Keep the A/B/C → model mapping yourself and reveal it only in the final report.

Each judge returns per-plan findings plus per-divergence verdicts. Fold these into the buckets from step 3 — a council doesn't replace the convergence analysis, it pressure-tests it.

## 5. Report

Write the report to `docs/plans/council-<topic>.md` using the template in [REPORT-FORMAT.md](REPORT-FORMAT.md), and give the user a compressed summary in chat: how many decisions settled, the divergences with your recommendation each, and the best unique catches.

## 6. The final plan

Offer to draft the reconciled plan — `docs/plans/final-<topic>.md`: settled decisions adopted as-is, unique contributions folded in, and each divergence resolved.

Resolve divergences with the user, not for them: walk the open decisions one at a time, rubber-duck style — recommendation offered, user confirms or redirects. For a long list, offer to hand the open decisions to `/rubber-duck` as the interview agenda.

When the final plan is approved, offer the natural next step: `/to-issues` to break it into tickets, or `/to-prd` to publish it.
