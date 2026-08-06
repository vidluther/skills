#!/usr/bin/env python3
"""Analyze the full 2020-2026 health history: yearly/quarterly arcs, coverage, workouts."""
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

F = Path("/private/tmp/claude-501/-Users-vluther-Documents-Obsidian-Vault/d3b240f7-602a-4027-87f9-2e69beaeb3b5/scratchpad/exportAll/HealthAutoExport-2020-07-29-2026-08-05.json")
d = json.loads(F.read_text())["data"]
metrics = {m["name"]: m.get("data", []) for m in d["metrics"]}
workouts = d.get("workouts", [])
BLOCKS = "▁▂▃▄▅▆▇█"


def daily(name, key="qty"):
    return {r["date"][:10]: r[key] for r in metrics.get(name, []) if r.get(key) is not None}


def spark(v):
    lo, hi = min(v), max(v)
    r = (hi - lo) or 1
    return "".join(BLOCKS[min(7, int((x - lo) / r * 7.99))] for x in v)


S = {k: daily(n, key) for k, (n, key) in {
    "weight": ("weight_body_mass", "qty"), "fat": ("body_fat_percentage", "qty"),
    "lean": ("lean_body_mass", "qty"), "rhr": ("resting_heart_rate", "qty"),
    "hrv": ("heart_rate_variability", "qty"), "sleep": ("sleep_analysis", "totalSleep"),
    "steps": ("step_count", "qty"), "vo2": ("vo2_max", "qty"), "bmi": ("body_mass_index", "qty"),
}.items()}

print(f"metrics: {len(d['metrics'])} | workouts: {len(workouts)} | file 34 MB\n")
print("=== coverage by metric ===")
for k, s in sorted(S.items()):
    if s:
        days = sorted(s)
        print(f"  {k:>7}: {len(s):>5} days   {days[0]} → {days[-1]}")

bp = {r["date"][:10]: (r.get("systolic"), r.get("diastolic")) for r in metrics.get("blood_pressure", []) if r.get("systolic")}
print(f"  {'bp':>7}: {len(bp):>5} days   {min(bp)} → {max(bp)}" if bp else "  bp: none")

# yearly
print("\n=== YEARLY ===")
print("| Year | Weight | Fat% | Lean | RHR | HRV | Sleep | Steps | VO2 | Workouts | Train min |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
wy = defaultdict(lambda: {"n": 0, "min": 0})
for w in workouts:
    y = w["start"][:4]
    wy[y]["n"] += 1
    wy[y]["min"] += w.get("duration", 0) / 60

years = sorted({d[:4] for d in S["steps"]})
for y in years:
    def m(k, nd=1):
        v = [x for dd, x in S[k].items() if dd[:4] == y]
        return f"{mean(v):.{nd}f}" if v else "—"
    print(f"| {y} | {m('weight')} | {m('fat')} | {m('lean')} | {m('rhr',0)} | {m('hrv',0)} | {m('sleep')} | {m('steps',0)} | {m('vo2')} | {wy[y]['n']} | {wy[y]['min']:.0f} |")

# quarterly weight/fat for shape
print("\n=== QUARTERLY (weight / fat% / rhr) ===")
q = defaultdict(lambda: defaultdict(list))
for k in ["weight", "fat", "rhr", "vo2", "sleep"]:
    for dd, v in S[k].items():
        qq = f"{dd[:4]}-Q{(int(dd[5:7])-1)//3+1}"
        q[qq][k].append(v)
for qq in sorted(q):
    r = q[qq]
    def f(k, nd=1):
        return f"{mean(r[k]):.{nd}f}" if r[k] else "—"
    print(f"  {qq}: weight {f('weight'):>6}  fat {f('fat'):>5}  rhr {f('rhr',0):>3}  vo2 {f('vo2'):>5}  sleep {f('sleep')}")

print("\n=== weight sparkline (quarterly means) ===")
wq = [mean(q[x]["weight"]) for x in sorted(q) if q[x]["weight"]]
print(f"  {spark(wq)}  {wq[0]:.1f} → {wq[-1]:.1f} lb  (peak {max(wq):.1f}, low {min(wq):.1f})")
fq = [mean(q[x]["fat"]) for x in sorted(q) if q[x]["fat"]]
print(f"  {spark(fq)}  fat {fq[0]:.1f} → {fq[-1]:.1f} %")

print("\n=== workout types (all time) ===")
for k, v in Counter(w["name"] for w in workouts).most_common(12):
    print(f"  {k:<34} {v}")

print("\n=== BP over time (yearly means) ===")
by = defaultdict(list)
for dd, (s_, di) in bp.items():
    by[dd[:4]].append((s_, di))
for y in sorted(by):
    v = by[y]
    print(f"  {y}: {mean(x[0] for x in v):.0f}/{mean(x[1] for x in v):.0f}  ({len(v)} readings)")
