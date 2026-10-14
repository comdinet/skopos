"""PIT: full-screen overlay (1920x720), shown automatically only while the
pit limiter is engaged. Service info on top, the distance to your box big and
centred at the bottom."""

from ..dsl import JS, Rect, Screen, Text
from ..theme import (BAD, BG, GOOD, INFO, LABEL, OFF, PIT_BLUE, TEXT, WARN, argb)
from .common import bordered, panel, stat, value

G, R_, W_, T_ = argb(GOOD), argb(BAD), argb(WARN), argb(TEXT)

# Which distance to show: pit entry (needs iRacing Extra Properties, before
# pit road) or the pit box.
TARGET = """function pitTarget() {
  if (inStall()) { return { mode: 'stall', d: 0 }; }
  var e = XN('DistanceToPitEntry', NaN);
  if (!onPitRoad() && e > 0 && e < 3000) { return { mode: 'entry', d: e }; }
  var b = pitBoxDist();
  if (b === null) { return { mode: 'none', d: null }; }
  return { mode: b < -8 ? 'passed' : 'box', d: b };
}
"""
T = TARGET + " var t = pitTarget();"
SPEED = "var v = N('SpeedKmh', 0), lim = pitLimitKph();"


def build():
    items = []
    # banner
    items.append(Rect(0, 0, 1920, 76, fill=PIT_BLUE, name="Banner"))
    items.append(Text(40, 0, 1000, 76, "PIT LIMITER", size=48, weight="Bold", color=TEXT, name="Banner title"))
    items.append(value(1000, 0, 880, 76,
                       "var l = pitLimitKph(); return (onPitRoad() ? 'PIT ROAD' : 'APPROACHING PIT') + (l > 0 ? '   ·   LIMIT ' + Math.round(l) + ' km/h' : '');",
                       "PIT ROAD   ·   LIMIT 60 km/h", size=28, weight="SemiBold", align="r", refresh=250,
                       name="Banner info"))

    # service / fuel tiles
    F = "var f = fuelData();"
    tiles = [
        ("FUEL NOW", F + " return fx(f.fuel, 1) + ' L';", "38.4 L", None, None),
        ("ADD TO FINISH", F + " if (f.add === null || f.add === undefined) { return '—'; } return f.add > 0 ? '+' + fx(f.add, 1) + ' L' : 'enough';",
         "+6.2 L", F + " return (f.add !== null && f.add !== undefined && f.add > 0) ? '%s' : '%s';" % (R_, G), BAD),
        ("FUEL SET", "var v = TN('PitSvFuel', null); return (TN('dpFuelFill', 1) > 0 && v !== null && v > 0) ? '+' + fx(v, 1) + ' L' : 'none';",
         "+32.4 L", None, None),
        ("TYRES", "var n = 0, c = ['LF', 'RF', 'LR', 'RR']; for (var i = 0; i < 4; i++) { if (TN('dp' + c[i] + 'TireChange', 0) > 0) { n++; } }"
                  " return n === 0 ? 'none' : (n === 4 ? 'all 4' : n + ' tyres');", "all 4", None, None),
        ("REPAIRS", "var r = TN('PitRepairLeft', 0), o = TN('PitOptRepairLeft', 0);"
                    " return (r + o) > 0 ? fx(r + o, 1) + ' s' : (TN('dpFastRepair', 0) > 0 ? 'fast repair' : 'none');",
         "none", None, None),
    ]
    gap = 16
    w = (1888 - gap * (len(tiles) - 1)) / len(tiles)
    for k, (title, js, sample, cjs, scol) in enumerate(tiles):
        x = round(16 + k * (w + gap))
        items.append(panel(x, 92, round(w), 124, title + " tile", title=title))
        if bordered():
            items.append(value(x + 20, 112, w - 40, 88, js, sample, size=56, align="c", refresh=250,
                               color_js=cjs, sample_color=scol, name=title))
        else:
            items += stat(x + 20, 104, w - 40, title, js, sample, vsize=52, refresh=250, color_js=cjs, sample_color=scol)

    # distance hero: bottom, centred
    items.append(panel(16, 232, 1888, 480, "Distance panel"))
    items.append(value(16, 244, 1888, 30,
                       T + " return { entry: 'METRES TO PIT ENTRY', box: 'METRES TO PIT BOX', stall: 'IN PIT BOX', passed: 'PIT BOX', none: 'METRES TO PIT BOX' }[t.mode];",
                       "METRES TO PIT BOX", size=24, weight="SemiBold", color=LABEL, align="c", refresh=100,
                       name="Distance title"))
    dist_col = (" if (t.mode === 'stall') { return '%s'; } if (t.mode === 'passed') { return '%s'; }"
                " if (t.d === null) { return '%s'; } return t.d < 30 ? '%s' : (t.d < 100 ? '%s' : '%s');"
                % (G, R_, T_, G, W_, T_))
    items.append(value(16, 280, 1888, 262,
                       T + " if (t.mode === 'stall') { return 'STOP'; } if (t.mode === 'passed') { return 'PASSED'; }"
                       " return t.d === null ? '—' : '' + Math.max(0, Math.round(t.d));",
                       "142", size=250, align="c", color_js=T + dist_col, sample_color=TEXT, name="Distance"))
    items.append(value(16, 552, 1888, 46,
                       T + SPEED + " var st = TN('PlayerCarPitSvStatus', 0);"
                       " if (t.mode === 'stall') { return st === 2 ? 'SERVICE COMPLETE  —  GO' : (st === 1 ? 'SERVICE IN PROGRESS' : 'IN BOX'); }"
                       " if (t.mode === 'passed') { return 'You passed your box'; }"
                       " if (t.mode === 'entry') { var b = pitBoxDist(); return 'Pit entry ahead' + (b !== null && b > 0 ? '  ·  box ' + Math.round(b) + ' m after the line' : ''); }"
                       " if (onPitRoad() && lim > 0 && v > lim + 0.5) { return 'SLOW DOWN  —  over the limit'; }"
                       " if (t.d !== null && t.d < 40 && v > 15) { return 'BRAKE NOW'; }"
                       " return t.d === null ? 'Pit box position unknown' : 'Box ahead';",
                       "Box ahead", size=34, align="c", refresh=100,
                       color_js=T + SPEED + " if (t.mode === 'entry' || t.mode === 'passed') { return '%s'; }"
                       " if (onPitRoad() && lim > 0 && v > lim + 0.5) { return '%s'; }"
                       " return (t.mode === 'stall' && TN('PlayerCarPitSvStatus', 0) === 2) || (t.d !== null && t.d < 40 && v > 15) ? '%s' : '%s';"
                       % (T_, R_, G, T_),
                       sample_color=TEXT, name="Status"))
    bx, bw, by, bh = 56, 1808, 612, 44
    items.append(Rect(bx, by, bw, bh, fill=OFF, radius=10, name="Approach track"))
    fill_js = T + " if (t.mode === 'stall') { return %d; } if (t.d === null || t.mode === 'passed') { return 0; } return Math.max(0, Math.min(1, 1 - t.d / 300)) * %d;" % (bw, bw)
    items.append(Rect(bx, by, round(bw * (1 - 142 / 300)), bh, fill=WARN, radius=10, name="Approach bar",
                      bind={"Width": JS(fill_js),
                            "BackgroundColor": JS(T + " if (t.d === null) { return '%s'; } return (t.mode === 'stall' || t.d < 30) ? '%s' : (t.d < 100 ? '%s' : '%s');"
                                                  % (argb(INFO), G, W_, argb(INFO)))}))
    for m in (100, 30):
        mx = bx + round(bw * (1 - m / 300))
        items.append(Rect(mx - 1, by - 8, 2, bh + 16, fill=TEXT, name="Marker %d m" % m))
        items.append(Text(mx - 60, by + bh + 8, 120, 24, "%d m" % m, size=18, weight="SemiBold", color=LABEL, align="c",
                          name="Marker %d label" % m))

    trigger = JS("return limiterOn();")
    return Screen("PIT", items, role="overlay", trigger=trigger, bg=BG)
