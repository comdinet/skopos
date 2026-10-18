#!/usr/bin/env python3
"""Render every page with its sample data to docs/img/*.png for the README.

    python3 screenshots.py

Needs Google Chrome (headless). The font falls back to Barlow off Windows.
"""

import os
import subprocess
import sys
import tempfile

import build
from skopos.pages import screens
from skopos.theme import BG, H, W

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT = os.path.join(build.ROOT, "docs", "img")

SHOTS = [  # screen name -> png
    ("RACE", "race.png"),
    ("FUEL", "fuel.png"),
    ("TIMING", "timing.png"),
    ("WEATHER", "weather.png"),
    ("FIELD (garage)", "field.png"),
    ("PIT", "pit.png"),
    ("IDLE", "idle.png"),
]

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>html,body{margin:0;background:%(bg)s;overflow:hidden}
.scr{position:relative;width:%(w)dpx;height:%(h)dpx;overflow:hidden;color:#F2F4F7;
font-family:Bahnschrift,'Barlow',sans-serif;font-variant-numeric:tabular-nums}</style></head>
<body><div class="scr">%(body)s</div></body></html>"""


def main():
    by_name = {s.name: s for s in screens()}
    os.makedirs(OUT, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for name, png in SHOTS:
            src = os.path.join(tmp, png + ".html")
            with open(src, "w", encoding="utf-8") as f:
                f.write(PAGE % {"bg": BG, "w": W, "h": H, "body": by_name[name].to_html()})
            dst = os.path.join(OUT, png)
            subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                            "--force-device-scale-factor=1", "--window-size=%d,%d" % (W, H),
                            "--virtual-time-budget=5000", "--user-data-dir=" + os.path.join(tmp, "profile"),
                            "--screenshot=" + dst, "file://" + src],
                           check=True, capture_output=True)
            print("%-15s -> %s" % (name, os.path.relpath(dst, build.ROOT)))


if __name__ == "__main__":
    sys.exit(main())
