#!/usr/bin/env python3
"""Laps-left at the end of timed and lap-limited races (JavaScriptCore).

Laps left = laps still to drive, counting the one you're on:
  2 on the lap before the white flag, 1 on the white-flag lap, 0 after the flag.
"""

import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import build  # noqa: E402,F401
from skopos import jslib  # noqa: E402

JSC = "/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc"
T = "DataCorePlugin.GameRawData.Telemetry."
SL = "DataCorePlugin.GameRawData.CurrentSessionInfo._SessionLaps"

TIMED = {SL: "unlimited", "TotalLaps": 0, T + "LapBestLapTime": 99.0}
LAPS20 = {SL: "20", "TotalLaps": 20, T + "LapBestLapTime": 99.0, T + "SessionTimeRemain": 604800.0}

CASES = [
    # (description, data, expected laps left)
    ("timed, 30 s left, half way round", dict(TIMED, **{T + "SessionTimeRemain": 30.0, T + "LapDistPct": 0.5}), 2),
    ("timed, clock ran out, not at the line yet", dict(TIMED, **{T + "SessionTimeRemain": 0.0, T + "LapDistPct": 0.8}), 2),
    ("timed, white flag", dict(TIMED, **{T + "SessionTimeRemain": 0.0, T + "LapDistPct": 0.1, "Flag_White": 1}), 1),
    ("timed, checkered", dict(TIMED, **{T + "SessionTimeRemain": 0.0, T + "LapDistPct": 0.02, "Flag_Checkered": 1}), 0),
    ("timed, 250 s left, half way round", dict(TIMED, **{T + "SessionTimeRemain": 250.0, T + "LapDistPct": 0.5}), 5),
    ("20 laps, lap 19 half way", dict(LAPS20, **{T + "LapCompleted": 18, T + "LapDistPct": 0.5}), 2),
    ("20 laps, white flag (lap 20)", dict(LAPS20, **{T + "LapCompleted": 19, T + "LapDistPct": 0.3, "Flag_White": 1}), 1),
    ("20 laps, lap 1", dict(LAPS20, **{T + "LapCompleted": 0, T + "LapDistPct": 0.2}), 20),
]

SIM = r"""
var D = {};
function $prop(k) { var v = D[k]; return v === undefined ? null : v; }
function timespantoseconds(t) { return 0; }
var fn = new Function('root', %(code)s), out = [];
var cases = %(cases)s;
for (var i = 0; i < cases.length; i++) { D = cases[i]; out.push(fn({})); }
print(JSON.stringify(out));
"""


def main():
    src = SIM % {"code": json.dumps(jslib.program("return lapsLeft();")),
                 "cases": json.dumps([c[1] for c in CASES])}
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(src)
        path = f.name
    res = subprocess.run([JSC, path], capture_output=True, text=True)
    os.unlink(path)
    got = json.loads(res.stdout.strip().splitlines()[-1])
    ok = True
    for (desc, _, exp), g in zip(CASES, got):
        good = g == exp
        ok &= good
        print("%-44s expected %-3s got %-5s %s" % (desc, exp, g, "OK" if good else "WRONG"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
