#!/usr/bin/env python3
"""Consistent stats across 7 / 30 / 90 / lifetime windows."""
import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from statistics import mean

S = Path("/private/tmp/claude-501/-Users-vluther-Documents-Obsidian-Vault/997c3e32-f0b2-4459-8d77-9484671ecc0a/scratchpad")
ALL = json.loads((S / "exportAll/merged-through-2026-08-06.json").read_text())["data"]
M = {m["name"]: m.get("data", []) for m in ALL["metrics"]}
# confirmed guest on the scale (Vid, 2026-08-05) + one matching outlier
GUEST = {"2025-06-27", "2025-08-22", "2025-09-19", "2025-10-06"}
# physically impossible body-fat readings (Withings impedance failures)
BAD_FAT = {"2024-04-30", "2024-06-11"}
TODAY = date(2026, 8, 6)


def daily(name, key="qty", skip=frozenset()):
    return {r["date"][:10]: r[key] for r in M.get(name, [])
            if r.get(key) is not None and r["date"][:10] not in skip}


D = {
    "weight": daily("weight_body_mass", skip=GUEST),
    "fat": daily("body_fat_percentage", skip=GUEST | BAD_FAT),
    "lean": daily("lean_body_mass", skip=GUEST | BAD_FAT),
    "rhr": daily("resting_heart_rate"),
    "hrv": daily("heart_rate_variability"),
    "sleep": daily("sleep_analysis", "totalSleep"),
    "steps": daily("step_count"),
    "active": daily("active_energy"),
    "vo2": daily("vo2_max"),
}
bp = {r["date"][:10]: (r["systolic"], r["diastolic"]) for r in M.get("blood_pressure", []) if r.get("systolic")}
wo = defaultdict(list)
for w in ALL["workouts"]:
    kcal = w.get("activeEnergyBurned")
    kcal = kcal.get("qty") if isinstance(kcal, dict) else kcal
    wo[w["start"][:10]].append((w.get("duration", 0) / 60, kcal or 0))

WINDOWS = [("7 days", 7), ("30 days", 30), ("90 days", 90), ("lifetime", 99999)]

print("| Metric | " + " | ".join(w for w, _ in WINDOWS) + " |")
print("|---|" + "---|" * len(WINDOWS))


def window_days(n):
    start = TODAY - timedelta(days=n - 1)
    return {d for d in set().union(*[set(x) for x in D.values()]) | set(bp) | set(wo)
            if date.fromisoformat(d) >= start}


rows = defaultdict(list)
for label, n in WINDOWS:
    days = window_days(n)
    for k, s in D.items():
        v = [s[d] for d in days if d in s]
        if label == "lifetime":
            # lifetime column shows the HIGHEST ever recorded, not an average —
            # averages are skewed by uneven tracking density (Vid, 2026-08-06)
            rows[k].append((max(v), len(v)) if v else None)
        else:
            rows[k].append((mean(v), len(v)) if v else None)
    b = [bp[d] for d in days if d in bp]
    rows["bp"].append((mean(x[0] for x in b), mean(x[1] for x in b), len(b)) if b else None)
    sess = [x for d in days if d in wo for x in wo[d]]
    rows["workouts"].append((len(sess), sum(x[0] for x in sess), sum(x[1] for x in sess)))
    rows["_days"].append(len(days))

NAMES = {"weight": ("Weight (lb)", 1), "fat": ("Body fat %", 1), "lean": ("Lean mass (lb)", 1),
         "rhr": ("Resting HR", 0), "hrv": ("HRV (ms)", 0), "sleep": ("Sleep (h)", 1),
         "steps": ("Steps/day", 0), "active": ("Active kcal/day", 0), "vo2": ("VO₂ max", 1)}
for k, (nm, nd) in NAMES.items():
    cells = [f"{v[0]:.{nd}f} <sub>({v[1]}d)</sub>" if v else "—" for v in rows[k]]
    print(f"| {nm} | " + " | ".join(cells) + " |")
cells = [f"{v[0]:.0f}/{v[1]:.0f} <sub>({v[2]})</sub>" if v else "—" for v in rows["bp"]]
print("| Blood pressure | " + " | ".join(cells) + " |")
cells = [f"{n} · {m:.0f} min" for n, m, _ in rows["workouts"]]
print("| Workouts | " + " | ".join(cells) + " |")

print("\n=== start vs end per window (weight/fat/rhr) ===")
for label, n in WINDOWS:
    days = sorted(window_days(n))
    out = []
    for k in ["weight", "fat", "rhr", "vo2"]:
        s = D[k]
        v = [(d, s[d]) for d in days if d in s]
        if len(v) >= 2:
            out.append(f"{k} {v[0][1]:.1f}→{v[-1][1]:.1f}")
    print(f"  {label}: " + "  |  ".join(out))

print("\n=== lifetime extremes ===")
for k in ["weight", "fat", "rhr", "sleep", "steps"]:
    s = D[k]
    if s:
        lo = min(s.items(), key=lambda x: x[1])
        hi = max(s.items(), key=lambda x: x[1])
        print(f"  {k}: min {lo[1]:.1f} ({lo[0]})  max {hi[1]:.1f} ({hi[0]})  n={len(s)}")
print(f"  workouts: {sum(len(v) for v in wo.values())} sessions across {len(wo)} days, "
      f"{sum(x[0] for v in wo.values() for x in v)/60:.0f} hours total")
