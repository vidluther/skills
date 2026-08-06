#!/usr/bin/env python3
"""Generate sparklines/bars for the health dashboard from the 30-day export."""
import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from statistics import mean

S = Path("/private/tmp/claude-501/-Users-vluther-Documents-Obsidian-Vault/997c3e32-f0b2-4459-8d77-9484671ecc0a/scratchpad")
d = json.loads((S / "HealthAutoExport-2026-07-06-2026-08-05.json").read_text())
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
    n = round(v / vmax * width) if vmax else 0
    return "█" * n + "·" * (width - n)


days = sorted(daily("step_count"))
series = {k: daily(n, key) for k, (n, key) in {
    "weight": ("weight_body_mass", "qty"), "bodyfat": ("body_fat_percentage", "qty"),
    "rhr": ("resting_heart_rate", "qty"), "hrv": ("heart_rate_variability", "qty"),
    "sleep": ("sleep_analysis", "totalSleep"), "steps": ("step_count", "qty"),
    "active": ("active_energy", "qty"),
}.items()}

print("=== SPARKLINES (daily, Jul 6 → Aug 5) ===")
for k, s in series.items():
    v = [s[day] for day in sorted(s)]
    print(f"{k:>8}: {spark(v)}  {v[0]:.1f} → {v[-1]:.1f}  (min {min(v):.1f}, max {max(v):.1f}, n={len(v)})")

# weekly training bars
wk = defaultdict(lambda: {"min": 0, "kcal": 0, "n": 0})
for w in data["workouts"]:
    day = date.fromisoformat(w["start"][:10])
    mon = (day - timedelta(days=day.weekday())).isoformat()
    kcal = w.get("activeEnergyBurned")
    kcal = kcal.get("qty") if isinstance(kcal, dict) else kcal
    wk[mon]["min"] += w.get("duration", 0) / 60
    wk[mon]["kcal"] += kcal or 0
    wk[mon]["n"] += 1

print("\n=== WEEKLY TRAINING ===")
mx = max(v["min"] for v in wk.values())
for m in sorted(wk):
    v = wk[m]
    print(f"{m}  {bar(v['min'], mx)}  {v['min']:>4.0f} min  {v['n']:>2} sessions  {v['kcal']:>5.0f} kcal")

print("\n=== SLEEP vs 7h target ===")
sl = series["sleep"]
for day in sorted(sl)[-14:]:
    h = sl[day]
    print(f"{day}  {bar(h, 9, 14)}  {h:.1f}h {'⚠' if h < 6 else ''}")

print("\n=== ENERGY BALANCE (days with food logged) ===")
kin = daily("dietary_energy")
basal = daily("basal_energy_burned")
for day in sorted(kin):
    out = series['active'].get(day, 0) + basal.get(day, 0)
    print(f"{day}  in={kin[day]:.0f}  out={out:.0f}  net={kin[day]-out:+.0f}")

print("\n=== MACROS (logged days) ===")
for m in ["protein", "carbohydrates", "total_fat"]:
    s = daily(m)
    print(f"{m}: {[(k, round(v,1)) for k, v in sorted(s.items())]}")
