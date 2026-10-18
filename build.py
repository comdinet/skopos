#!/usr/bin/env python3
"""Build the SKOPOS SimHub dashboard.

    python3 build.py

Outputs
  dist/SKOPOS.simhubdash      double-click (or Dash Studio > Import) on Windows
  dist/SKOPOS/                the same dashboard as a plain folder
  build/mockups/project/    HTML mockups rendered from the same layout
"""

import json
import os
import shutil
import sys
import zipfile

from skopos import jslib
from skopos.dsl import uid
from skopos.pages import screens
from skopos.theme import ACCENT, BG, H, W, argb

NAME = "SKOPOS"
VERSION = "1.0.0"
SIMHUB_VERSION = "9.11.3"
ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
MOCK = os.path.join(ROOT, "build", "mockups")

# Computed once per frame by SimHub and shared by all formulas. Slow-changing
# session lookups are cached for a couple of seconds.
VARIABLES = [
    ("shift", "return shiftCalc();"),
    ("fuel", "return JSON.stringify(fuelCalc());"),
    ("fieldOrder", "return cached(2000, function () { return fieldOrderCalc(); });"),
    ("playerSlot", "return cached(2000, function () { return playerSlotCalc(); });"),
    ("numSlots", "return cached(2000, function () { return numSlotsCalc(); });"),
    ("lbCount", "return cached(2000, function () { return lbCountCalc(); });"),
    ("sessBest", "return cached(1000, function () { return JSON.stringify(sessBestCalc()); });"),
    ("myRef", "return refTrack();"),
    ("bbFade", "return changeFade('bb', N('BrakeBias', null), 2000);"),
    ("classes", "return cached(2000, function () { return classesCalc(); });"),
    ("fieldTiming", "return cached(1000, function () { return fieldTimingCalc(); });"),
]
jslib.fn("""function cached(ms, calc) {
  var now = new Date().getTime();
  if (typeof root === 'undefined') { return calc(); }
  if (root.cacheT && now - root.cacheT < ms) { return root.cacheV; }
  root.cacheV = calc(); root.cacheT = now;
  return root.cacheV;
}""")


def metadata(scr):
    return {
        "ScreenCount": float(len(scr)),
        "InGameScreensIndexs": [i for i, s in enumerate(scr) if s.role == "ingame"],
        "IdleScreensIndexs": [i for i, s in enumerate(scr) if s.role == "idle"],
        "MainPreviewIndex": 1,
        "IsOverlay": False,
        "OverlaySizeWarning": False,
        "MetadataVersion": 2.0,
        "EnableOnDashboardMessaging": True,
        "PitScreensIndexs": [],
        "SimHubVersion": SIMHUB_VERSION,
        "Category": NAME,
        "Title": NAME,
        "Description": "iRacing dash for a 12.3in 1920x720 bar display: race, fuel, timing, weather, "
                       "field (garage, multi-class) + pit limiter page",
        "Author": "SKOPOS",
        "Width": float(W),
        "Height": float(H),
        "DashboardVersion": VERSION,
    }


def dashboard(scr):
    return {
        "Variables": {"DashboardVariables": [
            {
                "VariableName": name,
                "EvaluateOnlyOnce": False,
                "OverrideWithParentDashboardVariableWhenAvailable": False,
                "ValueExpression": {"Expression": jslib.program(body), "Interpreter": 1},
                "EvaluateBeforeScreenRoles": False,
            } for name, body in VARIABLES
        ]},
        "DashboardDebugManager": {"WindowPositionSettings": {
            "IsFullScreen": False, "Position": "0,0,%d,%d" % (W // 2, H // 2), "TopMost": False,
            "AllowTransparency": False, "CloseOnMonitorLoss": False, "NoWindowActivate": False}},
        "Version": 2,
        "Id": uid("dashboard/" + NAME),
        "BaseHeight": H,
        "BaseWidth": W,
        "BackgroundColor": argb(BG),
        "Screens": [s.to_json() for s in scr],
        "SnapToGrid": False,
        "HideLabels": True,
        "ShowForeground": True,
        "ForegroundOpacity": 100.0,
        "ShowBackground": True,
        "BackgroundOpacity": 100.0,
        "ShowBoundingRectangles": False,
        "GridSize": 10,
        "Images": [],
        "Metadata": metadata(scr),
        "ShowOnScreenControls": True,
        "IsOverlay": False,
        "EnableClickThroughOverlay": True,
        "EnableOnDashboardMessaging": True,
    }


def write_dashboard(scr):
    folder = os.path.join(DIST, NAME)
    shutil.rmtree(folder, ignore_errors=True)
    os.makedirs(folder)
    files = {
        NAME + ".djson": json.dumps(dashboard(scr), indent=2, ensure_ascii=False),
        NAME + ".djson.metadata": json.dumps(metadata(scr), indent=2),
        NAME + ".djson.carclasses": "[]",
    }
    for fname, text in files.items():
        with open(os.path.join(folder, fname), "w", encoding="utf-8", newline="\r\n") as f:
            f.write(text)
    # .simhubdash = zip of the dashboard folder (SimHub writes Windows paths)
    pkg = os.path.join(DIST, NAME + ".simhubdash")
    with zipfile.ZipFile(pkg, "w", zipfile.ZIP_DEFLATED) as z:
        for fname in sorted(files):
            info = zipfile.ZipInfo(NAME + "\\" + fname, date_time=(2026, 9, 26, 12, 0, 0))
            info.create_system = 0
            info.compress_type = zipfile.ZIP_DEFLATED
            with open(os.path.join(folder, fname), "rb") as f:
                z.writestr(info, f.read())
    return folder, pkg


# ---------------------------------------------------------------- mockups ----

BOARDS = [  # screen name -> artboard file, title
    ("RACE", "Main.dc.html", "1 · Race"),
    ("FUEL", "Fuel.dc.html", "2 · Fuel"),
    ("TIMING", "Timing.dc.html", "3 · Timing (whole field: lap time, then iR)"),
    ("WEATHER", "Weather.dc.html", "4 · Weather"),
    ("FIELD (garage)", "Field.dc.html", "Field (garage only, multi-class only)"),
    ("PIT", "Pit.dc.html", "Pit overlay (only while pit limiter is on)"),
    ("IDLE", "Idle.dc.html", "Idle (iRacing not running)"),
]

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>SKOPOS {title}</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700;800&amp;display=swap" rel="stylesheet">
<style>
body{{margin:0}}
</style>
</helmet>
<div style="position: relative; width: {w}px; height: {h}px; overflow: hidden; background: {bg}; color: #F2F4F7; font-family: Bahnschrift, 'Barlow', sans-serif; font-variant-numeric: tabular-nums">
{body}
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":{w},"height":{h}}}}}'>
class Component extends DCLogic {{
renderVals() {{
return {{}};
}}
}}
</script>
</body>
</html>
"""


PROPOSALS = [  # (artboard file, title, page module, canvas x, canvas y) for style experiments
]


def proposal_screens():
    """Pages rendered in the 'bordered' look, for the mockup canvas only."""
    from skopos.pages import common
    import importlib
    out = []
    common.STYLE["mode"] = "bordered"
    try:
        for fname, title, mod, x, y in PROPOSALS:
            page = importlib.import_module("skopos.pages." + mod)
            out.append((fname, title, page.build(), x, y))
    finally:
        common.STYLE["mode"] = "flat"
    return out


def write_mockups(scr):
    by_name = {s.name: s for s in scr}
    proj = os.path.join(MOCK, "project")
    shutil.rmtree(MOCK, ignore_errors=True)
    os.makedirs(proj)
    boards, order = {}, []
    for k, (name, fname, title) in enumerate(BOARDS):
        s = by_name[name]
        with open(os.path.join(proj, fname), "w", encoding="utf-8") as f:
            f.write(PAGE.format(title=title, w=W, h=H, bg=BG, body=s.to_html()))
        boards[fname] = {"x": (k % 2) * (W + 80), "y": (k // 2) * (H + 120), "w": W, "h": H, "title": title}
        order.append(fname)
    for fname, title, screen, x, y in proposal_screens():
        with open(os.path.join(proj, fname), "w", encoding="utf-8") as f:
            f.write(PAGE.format(title=title, w=W, h=H, bg=BG, body=screen.to_html()))
        boards[fname] = {"x": x, "y": y, "w": W, "h": H, "title": title}
        order.append(fname)
    canvas = {
        "v": 3,
        "createdOnFiles": {"v": 1, "at": "2026-09-26T21:00:00Z"},
        "title": "iRacing Dash Mockups",
        "launch": {"view": "canvas"},
        "pages": [],
        "boards": boards,
        "order": order,
        "notes": {"title": {"x": 0, "y": -300, "text": "SKOPOS — SimHub dash for iRacing, %d×%d" % (W, H),
                            "kind": "title1", "maxW": 2 * W + 80}},
        "designSystems": [],
    }
    with open(os.path.join(proj, "canvas.json"), "w", encoding="utf-8") as f:
        json.dump(canvas, f, indent=1, ensure_ascii=False)
    return proj


def write_preview(scr):
    """Plain local HTML with every screen, for a quick look in a browser."""
    by_name = {s.name: s for s in scr}
    frames = []
    for fname, title, screen, x, y in proposal_screens():
        frames.append('<figure><figcaption>%s</figcaption><div class="scr" style="background:%s">%s</div></figure>'
                      % (title, BG, screen.to_html()))
    for name, _, title in BOARDS:
        frames.append(
            '<figure><figcaption>%s</figcaption><div class="scr" style="background:%s">%s</div></figure>'
            % (title, BG, by_name[name].to_html()))
    page = """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>SKOPOS preview</title>
<link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>body{margin:0;background:#1b1f24;color:#ccc;font:14px sans-serif}figure{margin:24px}
.scr{position:relative;width:%dpx;height:%dpx;overflow:hidden;color:#F2F4F7;font-family:Bahnschrift,'Barlow',sans-serif;
font-variant-numeric:tabular-nums}</style></head><body>%s</body></html>""" % (W, H, "\n".join(frames))
    path = os.path.join(ROOT, "build", "preview.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
    return path


def main():
    scr = screens()
    folder, pkg = write_dashboard(scr)
    proj = write_mockups(scr)
    write_preview(scr)
    n_items = sum(1 for _ in json.dumps(dashboard(scr)).split('"$type"')) - 1
    print("dashboard :", pkg, "(%d KB, %d screens, %d items)" % (os.path.getsize(pkg) // 1024, len(scr), n_items))
    print("folder    :", folder)
    print("mockups   :", proj)


if __name__ == "__main__":
    sys.exit(main())
