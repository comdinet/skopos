"""TYRES (1920x720): carcass temps (outer / middle / inner), wear, pressures and the pit
service plan. iRacing only updates tyre temps and wear when the car stops in
its pit box, so the page says so rather than pretending the data is live."""

from ..dsl import JS, Rect, Screen, Text
from ..theme import (ACCENT, DIM, GOOD, LABEL, OFF, TEXT, TYRE_T_COLD, TYRE_T_HOT, TYRE_T_OK, WARN, argb)
from .common import chrome_bottom, chrome_top, label, panel, stat, value

TYRE_COL = """function hx(v) { var s = Math.max(0, Math.min(255, v)).toString(16).toUpperCase(); return s.length < 2 ? '0' + s : s; }
function mixc(a, b, k) { return '#FF' + hx(Math.round(a[0] + (b[0] - a[0]) * k)) + hx(Math.round(a[1] + (b[1] - a[1]) * k)) + hx(Math.round(a[2] + (b[2] - a[2]) * k)); }
function tyreCol(t) {
  var c = [61, 165, 255], o = [43, 212, 107], h = [255, 77, 77];
  if (!(t > 0)) { return '#FF1E252E'; }
  if (t <= %(c)s) { return mixc(c, c, 0); }
  if (t < %(o)s) { return mixc(c, o, (t - %(c)s) / (%(o)s - %(c)s)); }
  if (t < %(h)s) { return mixc(o, h, (t - %(o)s) / (%(h)s - %(o)s)); }
  return mixc(h, h, 0);
}
""" % {"c": TYRE_T_COLD, "o": TYRE_T_OK, "h": TYRE_T_HOT}


def py_tyre_col(t):
    c, o, h = (61, 165, 255), (43, 212, 107), (255, 77, 77)

    def mix(a, b, k):
        return "#%02X%02X%02X" % tuple(round(a[i] + (b[i] - a[i]) * k) for i in range(3))
    if t <= TYRE_T_COLD:
        return mix(c, c, 0)
    if t < TYRE_T_OK:
        return mix(c, o, (t - TYRE_T_COLD) / (TYRE_T_OK - TYRE_T_COLD))
    if t < TYRE_T_HOT:
        return mix(o, h, (t - TYRE_T_OK) / (TYRE_T_HOT - TYRE_T_OK))
    return mix(h, h, 0)


CORNERS = [
    ("LF", "FRONT LEFT", 16, 46, [78, 84, 88], [0.93, 0.91, 0.90], 172),
    ("RF", "FRONT RIGHT", 652, 46, [92, 87, 81], [0.88, 0.90, 0.92], 172),
    ("LR", "REAR LEFT", 16, 362, [74, 79, 83], [0.95, 0.94, 0.94], 165),
    ("RR", "REAR RIGHT", 652, 362, [86, 82, 77], [0.93, 0.94, 0.95], 165),
]


def tyre_card(code, title, x, y, temps, wear, press):
    w, h = 612, 302
    left_side = code[0] == "L"
    zone = ["OUT", "MID", "IN"] if left_side else ["IN", "MID", "OUT"]
    avg_wear = sum(wear) / 3
    out = [panel(x, y, w, h, title + " card"), label(x + 24, y + 12, 300, title)]
    out.append(value(x + 300, y + 6, 288, 40,
                     "var a = TN('%swearL', null), b = TN('%swearM', null), c = TN('%swearR', null);"
                     " return a === null ? '\u2014' : Math.round((a + b + c) / 3 * 100) + '%%';" % (code, code, code),
                     "%d%%" % round(avg_wear * 100), size=32, align="r", refresh=1000, name=title + " wear"))
    bw, gap = 176, 18
    for k, part in enumerate("LMR"):
        bx = x + 24 + k * (bw + gap)
        t = temps[k]
        tj = "var t = TN('%stempC%s', null);" % (code, part)
        out.append(Rect(bx, y + 50, bw, 104, fill=py_tyre_col(t), radius=10, name="%s temp %s" % (code, part),
                        bind={"BackgroundColor": JS(TYRE_COL + tj + " return tyreCol(t);")}, refresh=1000))
        out.append(Text(bx, y + 54, bw, 64, "%d\u00b0" % t, size=50, weight="Bold", color="#0B0E12", align="c",
                        name="%s temp %s value" % (code, part),
                        bind={"Text": JS(tj + " return t === null ? '\u2014' : Math.round(t) + '\u00b0';")},
                        refresh=1000, sample={"text": "%d\u00b0" % t}))
        out.append(Text(bx, y + 120, bw, 28, zone[k], size=18, weight="SemiBold", color="#0B0E12", align="c",
                        name="%s zone %s" % (code, part)))
        wj = "var v = TN('%swear%s', null);" % (code, part)
        out.append(Rect(bx, y + 166, bw, 10, fill=OFF, radius=5, name="%s wear track %s" % (code, part)))
        out.append(Rect(bx, y + 166, round(bw * wear[k]), 10, fill=TEXT, radius=5, name="%s wear %s" % (code, part),
                        bind={"Width": JS(wj + " return v === null ? 0 : Math.max(0, Math.min(1, v)) * %d;" % bw)}, refresh=1000))
        out.append(Text(bx, y + 180, bw, 24, "%d%%" % round(wear[k] * 100), size=18, weight="SemiBold", color=LABEL,
                        align="c", name="%s wear text %s" % (code, part),
                        bind={"Text": JS(wj + " return v === null ? '' : Math.round(v * 100) + '%';")},
                        refresh=1000, sample={"text": "%d%%" % round(wear[k] * 100)}))
    py = y + 212
    out += stat(x + 24, py, 270, "COLD PRESSURE", "return fx(TN('%scoldPressure', null), 0) + ' kPa';" % code,
                "%d kPa" % press, vsize=34, refresh=1000)
    out += stat(x + 318, py, 270, "NEXT STOP",
                "var v = TN('dp%sTireColdPress', null); if (v === null) { return '\u2014'; } if (v > 1000) { v = v / 1000; }"
                " return (TN('dp%sTireChange', 0) > 0 ? '' : 'keep  ') + fx(v, 0) + ' kPa';" % (code, code),
                "%d kPa" % (press - 2), vsize=34, align="r", refresh=1000)
    return out


def build():
    items = chrome_top(4)
    for c in CORNERS:
        items += tyre_card(*c)

    rx = 1288
    items.append(panel(rx, 46, 616, 618, "Service panel"))
    items.append(label(rx + 24, 56, 400, "NEXT PIT STOP"))
    chips = [("LF", 0, 0), ("RF", 1, 0), ("LR", 0, 1), ("RR", 1, 1)]
    for code, cx, cy in chips:
        bx, by = rx + 24 + cx * 290, 88 + cy * 68
        items.append(Rect(bx, by, 278, 60, fill=ACCENT, radius=10, name="Change %s" % code,
                          bind={"BackgroundColor": JS("return TN('dp%sTireChange', 0) > 0 ? '%s' : '%s';"
                                                      % (code, argb(ACCENT), argb(OFF)))}, refresh=500))
        items.append(Text(bx, by, 278, 60, code, size=32, weight="Bold", color="#0B0E12", align="c",
                          name="Change %s text" % code,
                          bind={"TextColor": JS("return TN('dp%sTireChange', 0) > 0 ? '#FF0B0E12' : '%s';" % (code, argb(DIM)))},
                          refresh=500))
    items.append(value(rx + 24, 222, 568, 32,
                       "var n = 0, c = ['LF', 'RF', 'LR', 'RR']; for (var i = 0; i < 4; i++) { if (TN('dp' + c[i] + 'TireChange', 0) > 0) { n++; } }"
                       " return n === 0 ? 'No tyre change' : (n === 4 ? 'Four new tyres' : n + ' new tyres');",
                       "Four new tyres", size=24, weight="SemiBold", refresh=500, name="Tyre plan"))
    items.append(Rect(rx + 24, 264, 568, 1, fill="#1E252E", name="Service divider"))
    items += stat(rx + 24, 274, 270, "FUEL ADD",
                  "var v = TN('PitSvFuel', null); return (TN('dpFuelFill', 1) > 0 && v !== null) ? '+' + fx(v, 1) + ' L' : 'none';",
                  "+32.4 L", vsize=40, refresh=500)
    items += stat(rx + 318, 274, 270, "FAST REPAIR",
                  "return TN('dpFastRepair', 0) > 0 ? 'YES' : 'no';", "no", vsize=40, align="r", refresh=500)
    items += stat(rx + 24, 360, 270, "COMPOUND",
                  "var c = XP('Player_TireCompound', null); if (c !== null && c !== '') { return '' + c; } var i = TN('PlayerTireCompound', null); return i === null ? '\u2014' : (i === 0 ? 'Dry' : 'Compound ' + i);",
                  "Dry", vsize=40, refresh=2000)
    items += stat(rx + 318, 360, 270, "SETS LEFT",
                  "var v = TN('TireSetsAvailable', null); return v === null ? '\u2014' : (v >= 255 ? '\u221e' : '' + v);",
                  "\u221e", vsize=40, align="r", refresh=2000)
    items += stat(rx + 24, 446, 270, "LAPS ON TYRES", "return fx(XN('Player_LapsSinceLastPit', null), 0);", "12", vsize=40, refresh=2000)
    items += stat(rx + 318, 446, 270, "TEAR-OFF", "return TN('dpWindshieldTearoff', 0) > 0 ? 'YES' : 'no';", "no",
                  vsize=40, align="r", refresh=500)

    items.append(Rect(rx + 24, 540, 568, 1, fill="#1E252E", name="Legend divider"))
    for k, (t, txt) in enumerate(((TYRE_T_COLD, "cold"), (TYRE_T_OK, "optimal"), (TYRE_T_HOT, "hot"))):
        lx = rx + 24 + k * 190
        items.append(Rect(lx, 558, 24, 24, fill=py_tyre_col(t), radius=6, name="Legend %s" % txt))
        items.append(Text(lx + 34, 554, 150, 32, "%d\u00b0 %s" % (t, txt), size=20, weight="SemiBold", color=LABEL,
                          name="Legend %s text" % txt))
    items.append(Text(rx + 24, 600, 568, 28, "Temps and wear update when you stop", size=20, weight="SemiBold",
                      color=LABEL, name="Note 1"))
    items.append(Text(rx + 24, 626, 568, 28, "in your pit box (iRacing limitation).", size=20, weight="SemiBold",
                      color=LABEL, name="Note 2"))

    items += chrome_bottom("TYRES")
    return Screen("TYRES", items)
