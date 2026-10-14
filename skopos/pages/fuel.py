"""FUEL: strategy calculator for lap- and time-limited races (1920x720)."""

from ..dsl import JS, Rect, Screen, Text
from ..theme import (ACCENT, BAD, FUEL_MARGIN_LAPS, GOOD, LABEL, OFF, TEXT, WARN, argb)
from .common import chrome_bottom, panel, value

G, R_, T_, W_ = argb(GOOD), argb(BAD), argb(TEXT), argb(WARN)
F = "var f = fuelData();"


TW, TH = 468, 172                       # tiles: 4 x 2
TX = [8 + k * (TW + 10) for k in range(4)]
TY = [314, 496]


def tile(x, y, title, js, sample, sub_js=None, sub_sample="", color_js=None, sample_color=None):
    out = [panel(x, y, TW, TH, title + " tile", title=title)]
    out.append(value(x + 24, y + 34, TW - 48, 80, F + js, sample, size=64, refresh=250,
                     color_js=(F + color_js) if color_js else None, sample_color=sample_color, name=title))
    if sub_js:
        out.append(value(x + 24, y + 124, TW - 48, 32, F + sub_js, sub_sample, size=22, weight="SemiBold",
                         color=LABEL, refresh=500, name=title + " sub"))
    return out


def build():
    items = []
    hw = (1904 - 10) // 2          # two heroes side by side, full width
    ax = 8 + hw + 10

    # hero: fuel in tank
    items.append(panel(8, 14, hw, 290, "Tank panel", title="FUEL IN TANK"))
    items.append(value(32, 36, 640, 160, F + " return fx(f.fuel, 1);", "38.4", size=140, align="r",
                       refresh=100, name="Tank"))
    items.append(Text(684, 110, 100, 70, "L", size=56, weight="SemiBold", color=LABEL, name="Tank unit"))
    items.append(Rect(32, 204, hw - 48, 20, fill=OFF, radius=10, name="Tank track"))
    items.append(Rect(32, 204, round((hw - 48) * 0.72), 20, fill=ACCENT, radius=10, name="Tank bar",
                      bind={"Width": JS(F + " return Math.max(0, Math.min(1, f.tank || 0)) * %d;" % (hw - 48)),
                            "BackgroundColor": JS(F + " return (f.lof !== null && f.lof < 2) ? '%s' : '%s';" % (R_, argb(ACCENT)))},
                      refresh=250))
    items.append(value(32, 232, 460, 30,
                       F + " return f.cap ? Math.round((f.tank || 0) * 100) + '% of ' + fx(f.cap, 1) + ' L tank' : '';",
                       "72% of 53.3 L tank", size=22, weight="SemiBold", color=LABEL, refresh=500, name="Tank sub"))
    items.append(value(32, 264, hw - 48, 34,
                       F + " return f.need === null || f.need === undefined ? 'Race distance unknown (practice / open session)' : 'Needed to finish  ' + fx(f.need, 1) + ' L';",
                       "Needed to finish  44.6 L", size=26, weight="SemiBold", refresh=500, name="Need"))

    # hero: add at next stop
    items.append(panel(ax, 14, hw, 290, "Add panel", title="ADD AT NEXT STOP"))
    add_col = " return (f.add === null || f.add === undefined) ? '%s' : (f.add > 0 ? '%s' : '%s');" % (T_, R_, G)
    items.append(value(ax + 24, 36, 640, 160,
                       F + " if (f.add === null || f.add === undefined) { return '\u2014'; } return f.add > 0 ? fx(f.add, 1) : '0.0';",
                       "6.2", size=140, align="r", refresh=250, color_js=F + add_col, sample_color=BAD, name="Add"))
    items.append(Text(ax + 676, 110, 100, 70, "L", size=56, weight="SemiBold", color=LABEL, name="Add unit"))
    items.append(value(ax + 24, 206, hw - 48, 46,
                       F + " if (f.stops === null || f.stops === undefined) { return ''; }"
                       " return f.stops === 0 ? 'NO STOP NEEDED  \u00b7  +' + fx(-f.add / (f.per || 1), 1) + ' laps spare'"
                       " : (f.stops === 1 ? '1 STOP' : f.stops + ' STOPS');",
                       "1 STOP", size=36, weight="Bold", refresh=500,
                       color_js=F + " return f.stops === 0 ? '%s' : '%s';" % (G, W_), sample_color=WARN, name="Stops"))
    items.append(value(ax + 24, 262, hw - 48, 30,
                       F + " return 'includes %s lap safety margin';" % FUEL_MARGIN_LAPS,
                       "includes %s lap safety margin" % FUEL_MARGIN_LAPS, size=22, weight="SemiBold",
                       color=LABEL, refresh=5000, name="Margin"))

    # 4 x 2 tiles
    xs, ys = TX, TY
    tiles = [
        ("PER LAP (AVG)", " return fx(f.per, 2);", "2.61", " return 'L per lap';", "L per lap", None, None),
        ("LAST LAP", " return fx(f.last, 2);", "2.58",
         " return (f.last && f.per) ? sgn(f.last - f.per, 2) + ' vs average' : '';", "−0.03 vs average", None, None),
        ("LAPS ON FUEL", " return fx(f.lof, 1);", "14.7", " return 'at current average';", "at current average",
         " return (f.lof !== null && f.lof < 2) ? '%s' : '%s';" % (R_, T_), None),
        ("TIME ON FUEL", " return f.tof ? clockStr(f.tof) : '—';", "25:12", " return 'at reference pace';", "at reference pace", None, None),
        ("RACE LAPS LEFT", " var l = lapsLeft(); return l === null ? '\u2014' : '' + l;", "15",
         " if (f.laps === null || f.laps === undefined) { return ''; }"
         " return fx(f.laps, 1) + ' laps of distance  \u00b7  ' + (sessionLaps() > 0 ? 'lap race' : 'timed race');",
         "14.6 laps of distance  \u00b7  lap race", None, None),
        ("RACE TIME LEFT", " return f.tleft === null || f.tleft === undefined ? '—' : clockStr(f.tleft);", "23:14",
         " return ('' + P('SessionTypeName', '')).toUpperCase();", "RACE", None, None),
        ("SAVE TARGET", " return fx(f.save, 2);", "2.24",
         " return f.savePct === null || f.savePct === undefined ? 'L per lap to skip the stop' : 'L/lap to skip the stop  (' + sgn(f.savePct * 100, 0) + '%)';",
         "L/lap to skip the stop  (−14%)",
         " return (f.savePct !== null && f.savePct !== undefined && f.savePct > -0.08) ? '%s' : '%s';" % (G, T_), None),
        ("PIT WINDOW", " return f.wOpen ? 'L' + f.wOpen + '–' + f.wClose : (f.stops === 0 ? 'NONE' : '—');", "L18–24",
         " var lap = N('CompletedLaps', 0) + 1; if (!f.wOpen) { return ''; } return lap >= f.wOpen ? 'OPEN NOW' : 'opens in ' + (f.wOpen - lap) + ' laps';",
         "opens in 6 laps",
         " var lap = N('CompletedLaps', 0) + 1; return (f.wOpen && lap >= f.wOpen) ? '%s' : '%s';" % (G, T_), None),
    ]
    for k, (title, js, sample, sub, sub_s, cjs, scol) in enumerate(tiles):
        items += tile(xs[k % 4], ys[k // 4], title, js, sample, sub, sub_s, cjs, scol)

    items += chrome_bottom("FUEL")
    return Screen("FUEL", items)
