#!/usr/bin/env python3
"""Brake-bias change highlight over time (JavaScriptCore): steady -> nothing,
a change -> full highlight fading to nothing over 2 s, a new click restarts it."""

import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import build  # noqa: E402
from skopos import jslib  # noqa: E402
from skopos.pages import screens  # noqa: E402

JSC = "/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc"


def formulas():
    race = [s for s in screens() if s.name == "RACE"][0]
    out = {}
    for it in race.items:
        if getattr(it, "name", "") in ("BB change highlight", "BB"):
            d = it.to_json()
            key = "fill" if it.name == "BB change highlight" else "text"
            prop = "BackgroundColor" if key == "fill" else "TextColor"
            out[key] = d["Bindings"][prop]["Formula"]["Expression"]
    out["var"] = jslib.program(dict(build.VARIABLES)["bbFade"])
    return out


# (ms, brake bias)
TIMELINE = [(0, 54.2), (500, 54.2), (1000, 54.5), (2000, 54.5), (2900, 54.5), (3100, 54.5), (3500, 54.0), (4500, 54.0)]

SIM = r"""
var D = {}, now = 0;
Date = function () { this.t = now; }; Date.prototype.getTime = function () { return this.t; };
function $prop(k) { var v = D[k]; return v === undefined ? null : v; }
var f = %(f)s, tl = %(tl)s, out = {};
['withVars', 'noVars'].forEach(function (mode) {
  var vRoot = {}, fRoot = {}, tRoot = {}, vf = new Function('root', f['var']),
      ff = new Function('root', f.fill), tf = new Function('root', f.text), rows = [];
  for (var i = 0; i < tl.length; i++) {
    now = tl[i][0]; D = { 'BrakeBias': tl[i][1] };
    if (mode === 'withVars') { D['variable.bbFade'] = vf(vRoot); }
    rows.push([now, tl[i][1], ff(fRoot), tf(tRoot)]);
  }
  out[mode] = rows;
});
print(JSON.stringify(out));
"""


def main():
    src = SIM % {"f": json.dumps(formulas()), "tl": json.dumps(TIMELINE)}
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as fh:
        fh.write(src)
        path = fh.name
    res = subprocess.run([JSC, path], capture_output=True, text=True)
    os.unlink(path)
    out = json.loads(res.stdout.strip().splitlines()[-1])
    expected_alpha = {0: 0, 500: 0, 1000: 230, 2000: 115, 2900: 12, 3100: 0, 3500: 230, 4500: 115}
    ok = True
    for mode, rows in out.items():
        print("--", mode)
        for t, bb, fill, text in rows:
            alpha = int(fill[1:3], 16)
            good = abs(alpha - expected_alpha[t]) <= 2
            ok &= good
            print("  t=%4d ms  BB %.1f  highlight %s (alpha %3d)  number %s  %s"
                  % (t, bb, fill, alpha, text, "OK" if good else "WRONG"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
