#!/usr/bin/env python3
"""Cluster GPX routes by location to find repeat walks, and compare pace across them."""
import json
import re
from math import atan2, cos, radians, sin, sqrt
from pathlib import Path

S = Path("/private/tmp/claude-501/-Users-vluther-Documents-Obsidian-Vault/997c3e32-f0b2-4459-8d77-9484671ecc0a/scratchpad")


def haversine(a, b):
    (la1, lo1), (la2, lo2) = a, b
    R = 3958.8  # miles
    dla, dlo = radians(la2 - la1), radians(lo2 - lo1)
    h = sin(dla / 2) ** 2 + cos(radians(la1)) * cos(radians(la2)) * sin(dlo / 2) ** 2
    return 2 * R * atan2(sqrt(h), sqrt(1 - h))


routes = []
for g in sorted(S.glob("*.gpx")):
    pts = re.findall(r'lat="([\d.-]+)" lon="([\d.-]+)"><ele>([\d.-]+)', g.read_text())
    if not pts:
        continue
    coords = [(float(a), float(b)) for a, b, _ in pts]
    eles = [float(e) for _, _, e in pts]
    dist = sum(haversine(coords[i], coords[i + 1]) for i in range(len(coords) - 1))
    lats = [c[0] for c in coords]
    lons = [c[1] for c in coords]
    routes.append({
        "file": g.name, "date": re.search(r"(\d{8})_", g.name).group(1),
        "start": coords[0], "n": len(coords), "dist": dist,
        "centroid": (sum(lats) / len(lats), sum(lons) / len(lons)),
        "ele_range": (min(eles), max(eles)),
    })

# cluster by centroid proximity (0.3 mi)
clusters = []
for r in routes:
    for c in clusters:
        if haversine(r["centroid"], c[0]["centroid"]) < 0.3:
            c.append(r)
            break
    else:
        clusters.append([r])

# workout summaries from the 90-day export for pace/HR
w90 = json.loads((S.parent / "export90/HealthAutoExport-2026-05-07-2026-08-05.json").read_text())["data"]["workouts"]
walks = {}
for w in w90:
    if "Walk" in w["name"] and w.get("location") == "Outdoor" or "Outdoor Walk" == w["name"]:
        key = w["start"][:10]
        def q(x):
            return x.get("qty") if isinstance(x, dict) else x
        walks.setdefault(key, []).append({
            "start": w["start"][11:16], "min": w.get("duration", 0) / 60,
            "dist": q(w.get("distance")), "hr": q(w.get("avgHeartRate")),
            "speed": q(w.get("speed")), "temp": q(w.get("temperature")),
            "hum": q(w.get("humidity")), "elev": q(w.get("elevationUp")),
        })

print(f"{len(routes)} routes → {len(clusters)} distinct locations\n")
for i, c in enumerate(sorted(clusters, key=len, reverse=True), 1):
    lat, lon = c[0]["centroid"]
    print(f"LOCATION {i}: {len(c)} visit(s)  centroid {lat:.4f},{lon:.4f}  (maps: https://maps.google.com/?q={lat:.5f},{lon:.5f})")
    for r in sorted(c, key=lambda x: x["date"]):
        day = f"{r['date'][:4]}-{r['date'][4:6]}-{r['date'][6:]}"
        w = walks.get(day, [{}])
        w = w[0] if w else {}
        pace = (w.get("min") / w["dist"]) if w.get("dist") else None
        print(f"   {day}  {r['dist']:.2f} mi (gpx)  "
              f"{w.get('min',0):.0f} min  pace {pace:.1f} min/mi  " if pace else
              f"   {day}  {r['dist']:.2f} mi (gpx)", end="")
        if w:
            print(f"HR {w.get('hr') and round(w['hr'])}  {w.get('temp') and round(w['temp'])}°F  "
                  f"{w.get('hum') and round(w['hum'])}%  climb {w.get('elev') and round(w['elev'])}ft")
        else:
            print()
    print()
