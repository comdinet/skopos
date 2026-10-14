#!/usr/bin/env python3
"""Execute every JavaScript formula of the dashboard against simulated SimHub
data (JavaScriptCore), in several scenarios:

  full     realistic race data, iRacing Extra Properties installed
  noplugin same without iRacing Extra Properties
  novars   dashboard variables unavailable (older SimHub) -> local fallback
  empty    every property null (session loading / not in car)

Fails on exceptions and on values of the wrong type for the bound property.
"""

import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import build  # noqa: E402  (registers the cached() helper)
from skopos import jslib  # noqa: E402
from skopos.pages import screens  # noqa: E402

JSC = "/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc"

KINDS = {
    "Text": "text", "TextColor": "color", "BackgroundColor": "color", "Visible": "bool",
    "Width": "num", "Height": "num", "Top": "num", "Left": "num",
}


def collect():
    out = []

    def walk(items, screen, rep=None):
        for it in items:
            d = it.to_json() if hasattr(it, "to_json") else it
            walk_json(d, screen, rep)

    def walk_json(d, screen, rep):
        reps = d.get("Repetitions") or 0
        for prop, b in (d.get("Bindings") or {}).items():
            f = b["Formula"]
            if f.get("Interpreter") == 1:
                out.append({"screen": screen, "item": d.get("Name"), "prop": prop,
                            "kind": KINDS.get(prop, "any"), "code": f["Expression"], "rep": rep})
        for c in d.get("Childrens", []):
            walk_json(c, screen, reps if reps else rep)

    for s in screens():
        walk(s.items, s.name)
        if getattr(s, "enabled", None) is not None:
            out.append({"screen": s.name, "item": "(page enabled)", "prop": "Enabled", "kind": "bool",
                        "code": jslib.program(s.enabled.body), "rep": None})
        if s.trigger is not None:
            out.append({"screen": s.name, "item": "(overlay trigger)", "prop": "Trigger", "kind": "bool",
                        "code": jslib.program(s.trigger.body), "rep": None})
    for name, body in build.VARIABLES:
        out.append({"screen": "(variables)", "item": name, "prop": "Variable", "kind": "any",
                    "code": jslib.program(body), "rep": None})
    return out


def drivers():
    names = ["Alex Kowalski", "Mario Rossi", "Lando Norris2", "Kenji Tanaka", "You Driver", "Rui Silva", "Eva Novak",
             "Pace Car"]
    nums = ["11", "23", "7", "12", "44", "64", "3", "0"]
    lics = ["A 4.12", "A 3.41", "A 2.99", "B 3.20", "A 3.87", "D 2.41", "Pro 4.99", "R 0.00"]
    d = {}
    for i, (n, num, lic) in enumerate(zip(names, nums, lics)):
        b = "DataCorePlugin.GameRawData.SessionData.DriverInfo.Drivers%02d." % (i + 1)
        d[b + "UserName"] = n
        d[b + "CarNumber"] = num
        d[b + "CarIdx"] = i
        d[b + "IRating"] = 1500 + i * 300
        d[b + "LicString"] = lic
        d[b + "CarClassColor"] = "0xffda59" if i % 2 else 16767577
        d[b + "CarIsPaceCar"] = 1 if n == "Pace Car" else 0
        d[b + "IsSpectator"] = 0
        d[b + "CarScreenNameShort"] = ["Porsche 992 GT3R", "Ferrari 296 GT3", "BMW M4 GT3", "Audi R8 LMS EVO II", "Porsche 992 GT3R", "McLaren 720S GT3", "Mercedes-AMG GT3", ""][i]
        d[b + "CarScreenName"] = "Car %d" % i
        gtp = i in (1, 5)          # two slower-rated GTP cars, the rest GT3
        d[b + "CarClassID"] = 4029 if gtp else 2708
        d[b + "CarClassShortName"] = "GTP" if gtp else "GT3"
        d[b + "CarClassEstLapTime"] = 88.0 if gtp else 102.0
    return d


def full_data():
    T = "DataCorePlugin.GameRawData.Telemetry."
    S = "DataCorePlugin.GameRawData.SessionData."
    d = {
        "Rpms": 7450, "SpeedKmh": 187.3, "Gear": "4", "Throttle": 86, "Brake": 0, "Position": 3, "OpponentsCount": 24,
        "CurrentLap": 12, "CompletedLaps": 11, "TotalLaps": 30, "BrakeBias": 54.2, "TCLevel": 3, "ABSLevel": 4,
        "EngineMap": 2, "AirTemperature": 24.1, "RoadTemperature": 38.2, "SessionTypeName": "Race",
        "Fuel": 38.4, "PitLimiterOn": 0, "PlayerLeaderboardPosition": 3, "DataCorePlugin.GameRunning": True, "IsInPitLane": 0, "PlayerName": "You Driver", "TrackName": "Spa",
        "Flag_Yellow": 1, "CarSettings_CurrentDisplayedRPMPercent": 81, "CarSettings_RPMRedLineReached": 0,
        "DataCorePlugin.Computed.Fuel_LitersPerLap": 2.61, "DataCorePlugin.Computed.Fuel_LastLapConsumption": 2.58,
        T + "FuelLevel": 38.4, T + "LapDistPct": 0.42, T + "SessionTimeRemain": 1394.0,
        T + "LapBestLapTime": 101.455, T + "LapLastLapTime": 101.902, T + "LapCurrentLapTime": 62.418,
        T + "LapDeltaToBestLap": -0.9, T + "LapDeltaToBestLap_OK": True, T + "LapDeltaToSessionBestLap": -0.342, T + "LapDeltaToSessionBestLap_OK": True, T + "PlayerCarClassPosition": 2,
        T + "PlayerCarMyIncidentCount": 4, T + "PlayerCarSLFirstRPM": 6000, T + "PlayerCarSLShiftRPM": 7900,
        T + "TrackWetness": 1, T + "WindVel": 3.3, T + "WindDir": 5.5, T + "Precipitation": 0.0, T + "Skies": 1,
        T + "RelativeHumidity": 0.55, T + "FogLevel": 0.0, T + "AirPressure": 101325.0, T + "AirDensity": 1.191,
        T + "SessionTimeOfDay": 52320.0, T + "SolarAltitude": 0.59, T + "WeatherDeclaredWet": False,
        T + "PlayerCarInPitStall": False, T + "IsOnTrack": True, T + "IsInGarage": False, T + "OnPitRoad": False, T + "PlayerCarPitSvStatus": 0,
        T + "PitSvFuel": 32.4, T + "dpFuelFill": 1.0, T + "dpFastRepair": 0.0, T + "dpWindshieldTearoff": 0.0,
        T + "PitRepairLeft": 0.0, T + "PitOptRepairLeft": 0.0, T + "PlayerTireCompound": 0, T + "TireSetsAvailable": 255,
        T + "CarIdxPosition": [1, 2, 4, 5, 3, 18, 7, 0], T + "CarIdxOnPitRoad": [False] * 7 + [True],
        S + "DriverInfo.DriverCarIdx": 4, S + "DriverInfo.DriverCarFuelMaxLtr": 74.0,
        S + "DriverInfo.DriverCarMaxFuelPct": 0.72, S + "DriverInfo.DriverPitTrkPct": 0.47,
        S + "DriverInfo.DriverCarEstLapTime": 102.0, S + "DriverInfo.DriverCarSLFirstRPM": 6000,
        S + "DriverInfo.DriverCarSLShiftRPM": 7900, S + "WeekendInfo.TrackLength": "7.00 km",
        S + "WeekendInfo.TrackPitSpeedLimit": "60.00 kph", S + "WeekendInfo.WeekendOptions.IncidentLimit": "17",
        S + "WeekendInfo.TrackDisplayShortName": "Spa",
        "DataCorePlugin.GameRawData.CurrentSessionInfo._SessionTrackRubberState": "moderate usage",
        "IRacingExtraProperties.iRacing_Player_LapsSinceLastPit": 12,
        "IRacingExtraProperties.iRacing_Player_iRGainEstimation": 24,
        "IRacingExtraProperties.iRacing_PitSpeedLimitKph": 60,
        "IRacingExtraProperties.iRacing_DistanceToPitEntry": 412,
        "IRacingExtraProperties.iRacing_DriverAhead_00_GapChangeLastLap": -0.21,
        "IRacingExtraProperties.iRacing_DriverAhead_00_LicenceString": "A 3.41",
        "PersistantTrackerPlugin.PreviousLap_00": {"ts": 101.902},
        "PersistantTrackerPlugin.PreviousLap_01": {"ts": 101.455},
    }
    for c in ("LF", "RF", "LR", "RR"):
        for p, v in (("L", 80), ("M", 85), ("R", 90)):
            d[T + c + "tempC" + p] = v
            d[T + c + "wear" + p] = 0.91
        d[T + c + "coldPressure"] = 172.0
        d[T + "dp" + c + "TireColdPress"] = 170000.0
        d[T + "dp" + c + "TireChange"] = 1.0
    for side, n in (("Ahead", 6), ("Behind", 6)):
        for k in range(n):
            b = "PersistantTrackerPlugin.Driver%s_%02d_" % (side, k)
            d[b + "Name"] = "Driver %s %d" % (side, k)
            d[b + "CarNumber"] = ["11", "23", "7", "12", "64", "3"][k]
            d[b + "Position"] = k + 1
            d[b + "Gap"] = (k + 1) * 1.1 * (-1 if side == "Ahead" else 1)
            d[b + "LastLapTime"] = {"ts": 101.5 + k}
            d[b + "IRating"] = 2000 + k * 100
            d[b + "LapsToPlayer"] = [0, 1, -1][k % 3]
    d.update(drivers())
    return d


LEADERBOARD = [
    # name, number, licence, iRating, last, best, gap to leader, current lap
    ("Alex Kowalski", "11", "A 4.12", 4210, 101.388, 101.022, 0.0, 12),
    ("Mario Rossi", "23", "A 3.41", 3322, 101.588, 101.310, 4.1, 12),
    ("You Driver", "44", "A 3.87", 2931, 101.902, 101.455, 5.4, 12),
    ("Lando Norris2", "7", "A 2.99", 3105, 101.744, 101.502, 6.0, 12),
    ("Kenji Tanaka", "12", "B 3.20", 2480, 102.030, 101.790, 11.7, 12),
    ("Rui Silva", "64", "D 2.41", 1320, 105.902, 104.100, 108.0, 11),
]


HARNESS = r"""
var __data = %(data)s;
var __repIndex = 1;
function $prop(k) { var v = __data[k]; if (v === undefined) { return null; } if (v && v.ts !== undefined) { return v; } return v; }
function timespantoseconds(t) { return t && t.ts !== undefined ? t.ts : 0; }
function repeatindex() { return __repIndex; }
var __lb = %(lb)s;
if (%(lbfuncs)s) {
  var __l = function (p) { return (p >= 1 && p <= __lb.length) ? __lb[p - 1] : null; };
  var __me = 3;
  drivername = function (p) { var d = __l(p); return d ? d[0] : null; };
  drivercarnumber = function (p) { var d = __l(p); return d ? d[1] : null; };
  driverlicencestring = function (p) { var d = __l(p); return d ? d[2] : null; };
  driveriracingirating = function (p) { var d = __l(p); return d ? d[3] : null; };
  drivercarclasscolor = function (p) { var d = __l(p); return d ? '#FFDA59' : null; };
  driverlastlap = function (p) { var d = __l(p); return d ? { ts: d[4] } : null; };
  driverbestlap = function (p) { var d = __l(p); return d ? { ts: d[5] } : null; };
  drivergaptoleader = function (p) { var d = __l(p); return d ? d[6] : null; };
  drivergaptoplayer = function (p) { var d = __l(p); return d ? d[6] - __lb[__me - 1][6] : null; };
  drivercurrentlap = function (p) { var d = __l(p); return d ? d[7] : null; };
  driverclassposition = function (p) { var d = __l(p); if (!d) { return null; } var gtp = (d[1] === '23' || d[1] === '64'), n = 0;
    for (var q = 0; q < p; q++) { var e = __lb[q], g = (e[1] === '23' || e[1] === '64'); if (g === gtp) { n++; } } return n; };
}
var __results = [];
var __formulas = %(formulas)s;
var __roots = [];
function __run(i, rep) {
  var f = __formulas[i];
  if (!__roots[i]) { __roots[i] = {}; }
  __repIndex = rep;
  var fn = new Function('root', f.code);
  return fn(__roots[i]);
}
function __check(kind, v) {
  if (kind === 'text') { return typeof v === 'string' || typeof v === 'number'; }
  if (kind === 'color') { return typeof v === 'string' && /^#[0-9A-F]{8}$/.test(v); }
  if (kind === 'bool') { return typeof v === 'boolean'; }
  if (kind === 'num') { return typeof v === 'number' && isFinite(v); }
  return v !== undefined;
}
// dashboard variables first, like SimHub
if (%(usevars)s) {
  for (var i = 0; i < __formulas.length; i++) {
    if (__formulas[i].prop === 'Variable') { __data['variable.' + __formulas[i].item] = __run(i, 1); }
  }
}
var __fail = 0, __n = 0, __samples = {};
for (var i = 0; i < __formulas.length; i++) {
  var f = __formulas[i], reps = f.rep ? f.rep : 1;
  for (var r = 1; r <= reps; r++) {
    __n++;
    try {
      var v = __run(i, r); v = __run(i, r);
      if (!__check(f.kind, v)) { __fail++; print('BADTYPE ' + f.screen + ' / ' + f.item + ' / ' + f.prop + ' rep ' + r + ' -> ' + JSON.stringify(v)); }
      else if (r === 1 || r === 6) { __samples[f.screen + ' / ' + f.item + ' / ' + f.prop + (reps > 1 ? ' #' + r : '')] = v; }
    } catch (e) { __fail++; print('ERROR ' + f.screen + ' / ' + f.item + ' / ' + f.prop + ' rep ' + r + ': ' + e); }
  }
}
print('RESULT ' + __n + ' evaluations, ' + __fail + ' failures');
if (%(dump)s) { print('SAMPLES ' + JSON.stringify(__samples)); }
"""


def run(name, data, usevars, formulas, dump=False, lb=True):
    src = HARNESS % {"lb": json.dumps(LEADERBOARD if lb else []), "lbfuncs": "true" if lb else "false",
                     "data": json.dumps(data), "formulas": json.dumps(formulas),
                     "usevars": "true" if usevars else "false", "dump": "true" if dump else "false"}
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(src)
        path = f.name
    out = subprocess.run([JSC, path], capture_output=True, text=True)
    os.unlink(path)
    text = out.stdout + out.stderr
    lines = [l for l in text.splitlines() if not l.startswith("SAMPLES ")]
    print("== %-9s" % name, "\n   ".join(lines[-12:]) if lines else "(no output)")
    samples = {}
    for l in text.splitlines():
        if l.startswith("SAMPLES "):
            samples = json.loads(l[8:])
    ok = "0 failures" in text
    return ok, samples


def main():
    formulas = collect()
    print("%d JavaScript formulas" % len(formulas))
    full = full_data()
    noplugin = {k: v for k, v in full.items() if not k.startswith("IRacingExtraProperties.")}
    results = [
        run("full", full, True, formulas, dump=True),
        run("noplugin", noplugin, True, formulas),
        run("novars", full, False, formulas),
        run("empty", {}, True, formulas, lb=False),
        run("nolbfuncs", full, True, formulas, lb=False),
    ]
    samples = results[0][1]
    with open(os.path.join(os.path.dirname(__file__), "last_samples.json"), "w") as f:
        json.dump(samples, f, indent=1, ensure_ascii=False)
    sys.exit(0 if all(ok for ok, _ in results) else 1)


if __name__ == "__main__":
    main()
