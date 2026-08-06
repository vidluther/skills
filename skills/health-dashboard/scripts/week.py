#!/usr/bin/env python3
"""7-day window: metrics, trends vs prior week, HR zones, logging gaps."""
import glob
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

DM = Path.home() / "Library/Mobile Documents/iCloud~com~ifunography~HealthExport/Documents/Daily Metrics"
DW = Path.home() / "Library/Mobile Documents/iCloud~com~ifunography~HealthExport/Documents/Daily Workouts"
E90 = Path("/private/tmp/claude-501/-Users-vluther-Documents-Obsidian-Vault/d3b240f7-602a-4027-87f9-2e69beaeb3b5/scratchpad/export90/HealthAutoExport-2026-05-07-2026-08-05.json")

# --- daily metrics from the 90-day export (complete history) + automation for recent
d90 = json.loads(E90.read_text())["data"]
m90 = {m["name"]: m.get("data", []) for m in d90["metrics"]}


def daily(name, key="qty"):
    return {r["date"][:10]: r[key] for r in m90.get(name, []) if r.get(key) is not None}


S = {k: daily(n, key) for k, (n, key) in {
    "weight": ("weight_body_mass", "qty"), "fat": ("body_fat_percentage", "qty"),
    "rhr": ("resting_heart_rate", "qty"), "hrv": ("heart_rate_variability", "qty"),
    "sleep": ("sleep_analysis", "totalSleep"), "steps": ("step_count", "qty"),
    "active": ("active_energy", "qty"), "water": ("dietary_water", "qty"),
    "kcal_in": ("dietary_energy", "qty"), "protein": ("protein", "qty"),
    "exercise_min": ("apple_exercise_time", "qty"),
}.items()}

WEEK = [f"2026-07-{d}" for d in (30, 31)] + [f"2026-08-0{d}" for d in range(1, 6)]
PREV = [f"2026-07-{d}" for d in range(23, 30)]

print("=== 7-DAY (Jul 30 – Aug 5) vs PRIOR 7 ===")
for k, s in S.items():
    cur = [s[d] for d in WEEK if d in s]
    prev = [s[d] for d in PREV if d in s]
    if cur:
        c, p = mean(cur), (mean(prev) if prev else None)
        delta = f"{c - p:+.1f}" if p else "—"
        print(f"  {k:>12}: {c:>8.1f}  (prev {p:.1f} → {delta})" if p else f"  {k:>12}: {c:>8.1f}  (n={len(cur)})")
        print(f"                days logged: {len(cur)}/7")

# --- workouts in window
wk = defaultdict(list)
for w in d90["workouts"]:
    day = w["start"][:10]
    if day in WEEK or day in PREV:
        kcal = w.get("activeEnergyBurned")
        kcal = kcal.get("qty") if isinstance(kcal, dict) else kcal
        wk[day].append({"name": w["name"], "min": w.get("duration", 0) / 60, "kcal": kcal or 0})

print("\n=== workouts ===")
for period, label in [(WEEK, "this week"), (PREV, "prior week")]:
    tot_min = sum(s["min"] for d in period for s in wk.get(d, []))
    tot_n = sum(len(wk.get(d, [])) for d in period)
    tot_k = sum(s["kcal"] for d in period for s in wk.get(d, []))
    print(f"  {label}: {tot_n} sessions, {tot_min:.0f} min, {tot_k:.0f} kcal")

# --- HR zones from per-second workout data
print("\n=== HR ZONES (from Daily Workouts per-second data) ===")
maxhr_observed = 0
for f in glob.glob(str(DW / "*.json")):
    for w in json.loads(Path(f).read_text())["data"].get("workouts", []):
        for s in w.get("heartRateData", []):
            maxhr_observed = max(maxhr_observed, s.get("Max", 0))
print(f"observed max HR across available data: {maxhr_observed}")

MAXHR = 170  # conservative estimate; see caveat
ZONES = [(0.50, 0.60, "Z1 very light"), (0.60, 0.70, "Z2 light/fat-burn"),
         (0.70, 0.80, "Z3 moderate/aerobic"), (0.80, 0.90, "Z4 hard/threshold"), (0.90, 1.01, "Z5 max")]

for f in sorted(glob.glob(str(DW / "*.json"))):
    data = json.loads(Path(f).read_text())["data"]
    for w in data.get("workouts", []):
        hrd = w.get("heartRateData") or []
        if not hrd:
            continue
        zt = defaultdict(int)
        below = 0
        for s in hrd:
            hr = s.get("Avg", 0)
            pct = hr / MAXHR
            if pct < 0.50:
                below += 1
                continue
            for lo, hi, name in ZONES:
                if lo <= pct < hi:
                    zt[name] += 1
                    break
        total = len(hrd)
        print(f"\n  {w['start'][:10]} {w['name']} ({w.get('duration',0)/60:.0f} min, {total} HR samples)")
        print(f"    below Z1 (<50% max, i.e. resting/paused): {below/total*100:.0f}%")
        for lo, hi, name in ZONES:
            if zt[name]:
                print(f"    {name:<22} {zt[name]/total*100:>5.1f}%  ({int(lo*MAXHR)}–{int(hi*MAXHR)} bpm)")

print("\n=== LOGGING GAPS (last 7 days) ===")
for k in ["kcal_in", "protein", "water"]:
    logged = [d for d in WEEK if d in S[k]]
    print(f"  {k}: {len(logged)}/7 days" + (f" — {logged}" if logged else " — NONE"))
bp = {r["date"][:10] for r in m90.get("blood_pressure", [])}
print(f"  blood_pressure: {len([d for d in WEEK if d in bp])}/7 days (last reading overall: {max(bp) if bp else '—'})")
