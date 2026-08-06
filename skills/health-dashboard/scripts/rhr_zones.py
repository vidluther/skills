#!/usr/bin/env python3
"""Daily RHR detail + HR zones recalibrated to measured max HR 167."""
import glob
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev

E90 = Path("/private/tmp/claude-501/-Users-vluther-Documents-Obsidian-Vault/d3b240f7-602a-4027-87f9-2e69beaeb3b5/scratchpad/export90/HealthAutoExport-2026-05-07-2026-08-05.json")
DW = Path.home() / "Library/Mobile Documents/iCloud~com~ifunography~HealthExport/Documents/Daily Workouts"

d90 = json.loads(E90.read_text())["data"]
rhr = {r["date"][:10]: r["qty"] for m in d90["metrics"] if m["name"] == "resting_heart_rate" for r in m["data"]}

WEEK = ["2026-07-30", "2026-07-31"] + [f"2026-08-0{d}" for d in range(1, 6)]
PREV = [f"2026-07-{d}" for d in range(23, 30)]

print("=== daily resting HR ===")
for label, days in [("prior week", PREV), ("this week", WEEK)]:
    vals = [(d, rhr[d]) for d in days if d in rhr]
    v = [x[1] for x in vals]
    print(f"{label}: " + "  ".join(f"{d[-2:]}={x:.0f}" for d, x in vals))
    print(f"   mean {mean(v):.1f}  sd {pstdev(v):.1f}  range {min(v):.0f}–{max(v):.0f}")

all30 = [rhr[d] for d in sorted(rhr) if d >= "2026-07-06"]
print(f"\n30-day: mean {mean(all30):.1f}, sd {pstdev(all30):.1f}, range {min(all30):.0f}–{max(all30):.0f}")

MAXHR = 167
RESTHR = 66
ZONES = [(0.50, 0.60, "Z1 very light"), (0.60, 0.70, "Z2 light"),
         (0.70, 0.80, "Z3 aerobic"), (0.80, 0.90, "Z4 threshold"), (0.90, 1.01, "Z5 max")]

print(f"\n=== HR ZONES @ max {MAXHR} (measured) ===")
for lo, hi, n in ZONES:
    print(f"  {n:<16} {int(lo*MAXHR):>3}–{int(hi*MAXHR):>3} bpm")

# Karvonen (heart-rate reserve) for comparison
print(f"\n=== same zones by heart-rate reserve (Karvonen, rest {RESTHR}) ===")
for lo, hi, n in ZONES:
    print(f"  {n:<16} {int(RESTHR + lo*(MAXHR-RESTHR)):>3}–{int(RESTHR + hi*(MAXHR-RESTHR)):>3} bpm")

print("\n=== recalculated session zones ===")
for f in sorted(glob.glob(str(DW / "*.json"))):
    for w in json.loads(Path(f).read_text())["data"].get("workouts", []):
        hrd = w.get("heartRateData") or []
        if not hrd:
            continue
        zt = defaultdict(int)
        below = 0
        for s in hrd:
            pct = s.get("Avg", 0) / MAXHR
            if pct < 0.50:
                below += 1
                continue
            for lo, hi, n in ZONES:
                if lo <= pct < hi:
                    zt[n] += 1
                    break
        t = len(hrd)
        print(f"\n{w['start'][:10]} {w['name']} ({w.get('duration',0)/60:.0f} min)")
        print(f"  below Z1 (<84 bpm): {below/t*100:.1f}%")
        for lo, hi, n in ZONES:
            if zt[n]:
                print(f"  {n:<16} {zt[n]/t*100:>5.1f}%  ({int(lo*MAXHR)}–{int(hi*MAXHR)} bpm)")
