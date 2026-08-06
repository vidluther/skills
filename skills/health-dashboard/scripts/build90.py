#!/usr/bin/env python3
"""Profile + build rollups from the 90-day export."""
import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from statistics import mean

S = Path("/private/tmp/claude-501/-Users-vluther-Documents-Obsidian-Vault/997c3e32-f0b2-4459-8d77-9484671ecc0a/scratchpad")
d = json.loads((S / "HealthAutoExport-2026-05-07-2026-08-05.json").read_text())
data = d["data"]
by_metric = {m["name"]: m.get("data", []) for m in data["metrics"]}
BLOCKS = "▁▂▃▄▅▆▇█"


def daily(name, key="qty"):
    return {r["date"][:10]: r[key] for r in by_metric.get(name, []) if r.get(key) is not None}


def spark(vals):
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1
    return "".join(BLOCKS[min(7, int((v - lo) / rng * 7.99))] for v in vals)


def bar(v, vmax, width=18):
    return "█" * (round(v / vmax * width) if vmax else 0) + "·" * (width - (round(v / vmax * width) if vmax else 0))


series = {k: daily(n, key) for k, (n, key) in {
    "weight": ("weight_body_mass", "qty"), "bodyfat": ("body_fat_percentage", "qty"),
    "lean": ("lean_body_mass", "qty"), "rhr": ("resting_heart_rate", "qty"),
    "hrv": ("heart_rate_variability", "qty"), "sleep": ("sleep_analysis", "totalSleep"),
    "steps": ("step_count", "qty"), "active": ("active_energy", "qty"),
    "vo2": ("vo2_max", "qty"), "kcal_in": ("dietary_energy", "qty"),
}.items()}

print("=== coverage ===")
print(f"metrics: {len(data['metrics'])}, workouts: {len(data['workouts'])}")
for k, s in series.items():
    if s:
        days = sorted(s)
        print(f"  {k:>8}: {len(s):>3} days  {days[0]} → {days[-1]}")

bp = {r["date"][:10]: (r.get("systolic"), r.get("diastolic")) for r in by_metric.get("blood_pressure", []) if r.get("systolic")}
print(f"  {'bp':>8}: {len(bp):>3} days  {min(bp) if bp else '-'} → {max(bp) if bp else '-'}")

# monthly + weekly
wk = defaultdict(lambda: defaultdict(list))
wkout = defaultdict(lambda: {"min": 0, "kcal": 0, "n": 0})
for w in data["workouts"]:
    dt = date.fromisoformat(w["start"][:10])
    mon = (dt - timedelta(days=dt.weekday())).isoformat()
    kcal = w.get("activeEnergyBurned")
    kcal = kcal.get("qty") if isinstance(kcal, dict) else kcal
    wkout[mon]["min"] += w.get("duration", 0) / 60
    wkout[mon]["kcal"] += kcal or 0
    wkout[mon]["n"] += 1

alldays = sorted(set().union(*[set(s) for s in series.values() if s]))
for day in alldays:
    dt = date.fromisoformat(day)
    mon = (dt - timedelta(days=dt.weekday())).isoformat()
    for k, s in series.items():
        if day in s:
            wk[mon][k].append(s[day])
    if day in bp:
        wk[mon]["bp_s"].append(bp[day][0]); wk[mon]["bp_d"].append(bp[day][1])


def f(v, nd=0):
    return f"{mean(v):.{nd}f}" if v else "—"


print("\n=== WEEKLY TABLE ===")
print("| Week | Sess | Min | Steps | Weight | Fat% | Lean | RHR | HRV | Sleep | BP |")
print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
for m in sorted(set(list(wk) + list(wkout))):
    v, o = wk[m], wkout[m]
    bpst = f"{f(v['bp_s'])}/{f(v['bp_d'])}" if v["bp_s"] else "—"
    print(f"| {m} | {o['n']} | {o['min']:.0f} | {f(v['steps'])} | {f(v['weight'],1)} | {f(v['bodyfat'],1)} | {f(v['lean'],1)} | {f(v['rhr'])} | {f(v['hrv'])} | {f(v['sleep'],1)} | {bpst} |")

print("\n=== SPARKS (weekly means over 13 weeks) ===")
weeks = sorted(wk)
for k in ["weight", "bodyfat", "lean", "rhr", "hrv", "sleep", "steps", "vo2"]:
    vals = [mean(wk[w][k]) for w in weeks if wk[w][k]]
    if len(vals) > 2:
        print(f"{k:>8}: {spark(vals)}  {vals[0]:.1f} → {vals[-1]:.1f}")

print("\n=== WEEKLY TRAINING BARS ===")
mx = max(v["min"] for v in wkout.values())
for m in sorted(wkout):
    v = wkout[m]
    print(f"{m}  {bar(v['min'], mx)}  {v['min']:>4.0f} min · {v['n']:>2} sess · {v['kcal']:>5.0f} kcal")

print("\n=== workout type totals ===")
tot = defaultdict(lambda: [0, 0])
for w in data["workouts"]:
    tot[w["name"]][0] += 1
    tot[w["name"]][1] += w.get("duration", 0) / 60
for k, (n, mins) in sorted(tot.items(), key=lambda x: -x[1][1]):
    print(f"  {k:<32} {n:>3} sessions  {mins:>6.0f} min")

print("\n=== nutrition logged days:", sorted(series["kcal_in"]))
print("=== last 10 BP:", sorted(bp.items())[-10:])
