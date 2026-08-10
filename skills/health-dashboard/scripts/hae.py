#!/usr/bin/env python3
"""Reader for Health Auto Export's AutoSync `.hae` store.

AutoSync is the fallback in the pipeline doc, but as of 2026-08-06 it is the *reliable*
source: the hourly `dm_-YYYY-MM-DD.json` automation degraded four times in one day
(step/energy streams truncated to the last hour), while AutoSync kept full coverage.

Two file formats exist and both must be handled:

  legacy  bare LZFSE stream                     -> `compression_tool -decode` works directly
  HAE1    b"HAE1" + repeated (uint32be len + LZFSE chunk), one chunk per hour
          (appeared 2026-08-06 ~19:19; whole-file decode fails with
           "could not auto-detect compression type")

Dates are Apple epoch: add 978307200 for Unix time.

Reads only; prints to stdout. Run directly for a 7-day table:

    python3 hae.py                 # last 7 days ending today
    python3 hae.py 20260806        # last 7 days ending on a given day
"""

import collections
import datetime
import glob
import json
import os
import struct
import subprocess
import sys
import tempfile

BASE = os.path.expanduser(
    "~/Library/Mobile Documents/iCloud~com~ifunography~HealthExport/Documents/AutoSync/HealthMetrics"
)
APPLE_EPOCH = 978307200
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

# Every sample is emitted once per unit. Keep exactly one, lowest rank wins.
UNIT_RANK = {
    "lb": 0, "kcal": 0, "count": 0, "g": 0, "mmHg": 0, "%": 0,
    "ms": 0, "hr": 0, "count/min": 0, "mi": 0,
    "kg": 1, "kJ": 1, "km": 1,
    "st": 2,
}

# How each metric collapses to one number per day.
#   sum     union unique samples across all files, add them up (cumulative streams)
#   mean    union unique samples, average them
#   latest  the newest file wins outright (Apple revises these in place during the day)
#   reading discrete readings; identical values close in time are one event double-synced
AGG = {
    "step_count": "sum",
    "active_energy": "sum",
    "basal_energy_burned": "sum",
    "dietary_energy": "sum",
    "protein": "sum",
    "fiber": "sum",
    "carbohydrates": "sum",
    "total_fat": "sum",
    "apple_exercise_time": "sum",
    "heart_rate_variability": "mean",
    "respiratory_rate": "mean",
    "resting_heart_rate": "latest",
    "walking_heart_rate_average": "latest",
    "vo2_max": "latest",
    "sleep_analysis": "latest",
    "weight_body_mass": "reading",
    "body_fat_percentage": "reading",
    "lean_body_mass": "reading",
    "blood_pressure": "reading",
}

_CACHE_DIR = os.path.join(tempfile.gettempdir(), "hae-cache")
_MEM = {}


def _lzfse(buf):
    """Decode one LZFSE stream via compression_tool. Returns bytes or None."""
    os.makedirs(_CACHE_DIR, exist_ok=True)
    src = os.path.join(_CACHE_DIR, "_chunk.in")
    dst = os.path.join(_CACHE_DIR, "_chunk.out")
    with open(src, "wb") as fh:
        fh.write(buf)
    r = subprocess.run(
        ["compression_tool", "-decode", "-i", src, "-o", dst],
        capture_output=True,
    )
    if r.returncode != 0:
        return None
    with open(dst, "rb") as fh:
        return fh.read()


def records(path):
    """All JSON records in a `.hae` file, either format. Cached by path+mtime."""
    key = (path, os.path.getmtime(path))
    if key in _MEM:
        return _MEM[key]

    with open(path, "rb") as fh:
        raw = fh.read()

    out = []
    if raw[:4] == b"HAE1":
        off = 4
        while off + 4 <= len(raw):
            (n,) = struct.unpack(">I", raw[off:off + 4])
            off += 4
            blob = raw[off:off + n]
            off += n
            if not blob:
                break
            d = _lzfse(blob)
            if d:
                try:
                    out.append(json.loads(d))
                except ValueError:
                    pass
    else:
        d = _lzfse(raw)
        if d:
            try:
                j = json.loads(d)
                out = j if isinstance(j, list) else [j]
            except ValueError:
                pass

    _MEM[key] = out
    return out


def files_for(metric, day):
    """Files for a metric/day, oldest first. Sorted by mtime — NOT by name:
    `20260806.hae` is the live file and is newer than `20260806 3.hae`."""
    pat = os.path.join(BASE, metric, "%s*.hae" % day)
    return sorted(glob.glob(pat), key=os.path.getmtime)


def samples(metric, day):
    """Unique samples for a metric on a day, one unit each, later files winning."""
    mode = AGG.get(metric, "sum")
    paths = files_for(metric, day)
    if not paths:
        return []
    if mode in ("latest", "reading") and mode == "latest":
        paths = paths[-1:]

    best = {}
    for path in paths:
        for rec in records(path):
            for p in rec.get("data", []):
                key = (p.get("start"), p.get("end"))
                unit = p.get("unit")
                cur = best.get(key)
                if cur is None or UNIT_RANK.get(unit, 9) <= UNIT_RANK.get(cur.get("unit"), 9):
                    best[key] = p
    out = list(best.values())
    out.sort(key=lambda p: p.get("start") or 0)

    if mode == "reading":
        out = _collapse_resyncs(out)
    return out


def _collapse_resyncs(pts, window=7200):
    """One physical reading synced by two apps arrives twice with different timestamps
    (195.0 lb at 08:33 via Yazio and again at 09:22 via MyFitnessPal). Same value within
    `window` seconds = one event."""
    kept = []
    for p in pts:
        sig = (
            round(p.get("qty", 0), 2),
            p.get("systolic"),
            p.get("diastolic"),
        )
        dup = False
        for q in kept:
            qsig = (
                round(q.get("qty", 0), 2),
                q.get("systolic"),
                q.get("diastolic"),
            )
            if sig == qsig and abs((p.get("start") or 0) - (q.get("start") or 0)) <= window:
                dup = True
                break
        if not dup:
            kept.append(p)
    return kept


def sleep_hours(day):
    """Hours slept in the night *ending* on `day` — Apple attributes a night to the
    wake date, and so does the dashboard.

    A day's `.hae` file holds two different nights: the one that ended that morning
    (00:00–~06:30) and the one that started that evening (~20:30 onwards, spilling past
    midnight). Summing a file whole double-counts. So: take segments ending before noon
    on `day`, drawn from both `day`'s file and the previous day's — the early part of the
    night lives in the previous day's file. The overlapping midnight segment appears in
    both and is deduped by (start, end)."""
    d = datetime.datetime.strptime(day, "%Y%m%d").date()
    prev = (d - datetime.timedelta(days=1)).strftime("%Y%m%d")
    noon = datetime.datetime.combine(d, datetime.time(12, 0), IST).timestamp() - APPLE_EPOCH
    dawn = noon - 24 * 3600  # nothing earlier than noon the day before counts

    seen = {}
    for src in (prev, day):
        for path in files_for("sleep_analysis", src):
            for rec in records(path):
                for p in rec.get("data", []):
                    end = p.get("end")
                    if end is None or not (dawn < end <= noon):
                        continue
                    seen[(p.get("start"), end)] = p
    if not seen:
        return None
    return sum(p.get("totalSleep", 0) for p in seen.values())


def daily(metric, day):
    """One number for the day, or None. `sleep_analysis` returns total hours."""
    if metric == "sleep_analysis":
        return sleep_hours(day)

    pts = samples(metric, day)
    if not pts:
        return None
    mode = AGG.get(metric, "sum")

    if metric == "blood_pressure":
        return (
            sum(p.get("systolic", 0) for p in pts) / len(pts),
            sum(p.get("diastolic", 0) for p in pts) / len(pts),
        )

    qtys = [p.get("qty", 0) for p in pts]
    if mode == "sum":
        return sum(qtys)
    if mode == "latest":
        return qtys[-1]
    return sum(qtys) / len(qtys)


def local(apple_ts):
    return datetime.datetime.fromtimestamp(apple_ts + APPLE_EPOCH, IST)


def _fmt(v, spec):
    return format(v, spec) if v is not None else "—".rjust(int(spec.split(".")[0] or 0))


def main(argv):
    end = (
        datetime.datetime.strptime(argv[1], "%Y%m%d").date()
        if len(argv) > 1
        else datetime.datetime.now(IST).date()
    )
    days = [(end - datetime.timedelta(days=i)).strftime("%Y%m%d") for i in range(6, -1, -1)]

    cols = [
        ("steps", "step_count", "7.0f"),
        ("active", "active_energy", "7.0f"),
        ("basal", "basal_energy_burned", "7.0f"),
        ("weight", "weight_body_mass", "7.1f"),
        ("fat%", "body_fat_percentage", "6.1f"),
        ("RHR", "resting_heart_rate", "5.0f"),
        ("HRV", "heart_rate_variability", "6.1f"),
        ("sleep", "sleep_analysis", "6.2f"),
        ("kcal in", "dietary_energy", "8.0f"),
        ("protein", "protein", "8.1f"),
        ("fiber", "fiber", "6.1f"),
    ]
    head = "%-10s" % "day" + "".join(
        h.rjust(int(spec.split(".")[0])) for h, _, spec in cols
    )
    print(head)
    print("-" * len(head))
    for d in days:
        row = "%-10s" % d
        for _, metric, spec in cols:
            row += _fmt(daily(metric, d), spec)
        print(row)

    print()
    for d in days:
        bp = daily("blood_pressure", d)
        if bp:
            n = len(samples("blood_pressure", d))
            print("BP %s: %.0f/%.0f (n=%d)" % (d, bp[0], bp[1], n))


if __name__ == "__main__":
    main(sys.argv)
