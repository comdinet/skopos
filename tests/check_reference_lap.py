#!/usr/bin/env python3
"""Lap-by-lap simulation of the 'your best' reference tracking (JavaScriptCore).

Scenario, with the delta computed the way iRacing does it (against your best
CLEAN lap of the session):
  lap 1  103.500  clean   -> becomes the reference
  lap 2  102.900  clean   -> faster, becomes the reference
  lap 3  101.800  1x      -> faster but with an incident: iRacing keeps 102.900
                             (LapBestLapTime says 101.800 - the old bug)
  lap 4  in progress at 60 %: predicted must be reference + delta
"""

import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import build  # noqa: E402,F401  (registers cached())
from skopos import jslib  # noqa: E402

JSC = "/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc"

T = "DataCorePlugin.GameRawData.Telemetry."
SIM = r"""
var D = {}, now = 0;
Date = function () { this.t = now; }; Date.prototype.getTime = function () { return this.t; };
function $prop(k) { var v = D[k]; return v === undefined ? null : v; }
function timespantoseconds(t) { return t && t.ts !== undefined ? t.ts : 0; }
var varRoot = {}, varFn = new Function('root', %(var)s), predFn = new Function('root', %(pred)s),
    bestFn = new Function('root', %(best)s);
function frame() { D['variable.myRef'] = varFn(varRoot); now += 16; }
var laps = [[103.5, 0], [102.9, 0], [101.8, 1]], ref = null, inc = 0, lapc = 0, out = [];
D['%(T)sSessionNum'] = 0; D['%(T)sLapCompleted'] = 0; D['%(T)sLapLastLapTime'] = -1;
D['%(T)sPlayerCarMyIncidentCount'] = 0;
for (var L = 0; L < laps.length; L++) {
  var t = laps[L][0];
  for (var f = 0; f <= 100; f++) {          // drive the lap
    var pct = f / 100.0;
    D['%(T)sLapDistPct'] = pct;
    D['%(T)sLapDeltaToSessionBestLap_OK'] = ref !== null;
    D['%(T)sLapDeltaToSessionBestLap'] = ref !== null ? (t - ref) * pct : 0;
    if (f === 50 && laps[L][1]) { inc += laps[L][1]; D['%(T)sPlayerCarMyIncidentCount'] = inc; }
    frame();
  }
  lapc++; D['%(T)sLapCompleted'] = lapc; D['%(T)sLapDistPct'] = 0.001; frame(); frame();   // cross the line
  D['%(T)sLapLastLapTime'] = t; D['%(T)sLapBestLapTime'] = Math.min(t, D['%(T)sLapBestLapTime'] || 999); frame();
  if (!laps[L][1] && (ref === null || t < ref)) { ref = t; }   // what iRacing does
  out.push({ lap: L + 1, time: t, iracingRef: ref, dashRef: +D['variable.myRef'] });
}
// lap 4, 60 pct in, running 0.25 s faster than the reference at this point
D['%(T)sLapDistPct'] = 0.6; D['%(T)sLapDeltaToSessionBestLap_OK'] = true; D['%(T)sLapDeltaToSessionBestLap'] = -0.25; frame();
print(JSON.stringify({ laps: out, predicted: predFn({}), yourBest: bestFn({}), lapBestLapTime: D['%(T)sLapBestLapTime'] }));
"""


def main():
    src = SIM % {
        "var": json.dumps(jslib.program("return refTrack();")),
        "pred": json.dumps(jslib.program("return predicted();")),
        "best": json.dumps(jslib.program("return myBest();")),
        "T": T,
    }
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(src)
        path = f.name
    res = subprocess.run([JSC, path], capture_output=True, text=True)
    os.unlink(path)
    if res.returncode or not res.stdout.strip():
        print(res.stdout, res.stderr)
        sys.exit(1)
    r = json.loads(res.stdout.strip().splitlines()[-1])
    ok = True
    for lap in r["laps"]:
        good = abs(lap["dashRef"] - lap["iracingRef"]) < 0.002
        ok &= good
        print("lap %d  %.3f   iRacing ref %.3f   dash ref %.3f   %s"
              % (lap["lap"], lap["time"], lap["iracingRef"], lap["dashRef"], "OK" if good else "MISMATCH"))
    exp = r["laps"][-1]["iracingRef"] - 0.25
    good = abs(r["predicted"] - exp) < 0.002 and abs(r["yourBest"] - r["laps"][-1]["iracingRef"]) < 0.002
    ok &= good
    print("lap 4 @60%%: predicted %.3f (expected %.3f), your best %.3f, LapBestLapTime %.3f   %s"
          % (r["predicted"], exp, r["yourBest"], r["lapBestLapTime"], "OK" if good else "MISMATCH"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
