"""RACE: the main driving page (1920x720). The only page with shift lights."""

from ..dsl import JS, NC, Rect, Screen, Text
from ..theme import (BAD, BG, GOOD, LABEL, LOW_IR, OFF, TEXT, WARN, argb)
from .common import (ACCENTS, BORDER, SHIFT_BLINK_MS, chrome_bottom, chrome_top, head_box, panel, stat, value)

G, R_, W_, T_ = argb(GOOD), argb(BAD), argb(WARN), argb(TEXT)

# grid: 8 px outer margin, 10 px gaps, content between the shift lights and the footer
TOP, BOT = 46, 668
LX, LW = 8, 608      # left column
CX, CW = 626, 660    # centre column
RX, RW = 1296, 616   # right column

# Shift point: the gear panel alternates red / yellow; text on it follows.
FLASH = "var s = shiftLeds(), fl = s >= 99, red = blinkOn(%d);" % SHIFT_BLINK_MS


def on_gear_panel(normal):
    return FLASH + " if (fl) { return red ? '%s' : '#FF0B0E12'; } return '%s';" % (T_, argb(normal))


def gap_box(x, y, w, h, side, samples):
    """Car directly ahead / behind ON TRACK (relative)."""
    title = "CAR AHEAD" if side == "ahead" else "CAR BEHIND"
    k = "'Ahead_00'" if side == "ahead" else "'Behind_00'"
    on = "nearOn(%s)" % k
    low = "var ir = %s ? parseFloat(nearIR(%s)) : 0; return ir > 0 && ir < %d" % (on, k, LOW_IR)
    low_sample = int(samples[5]) < LOW_IR
    return [
        panel(x, y, w, h, title + " panel", title=title),
        value(x + 24, y + 12, w - 48, 26,
              "if (!%s) { return ''; } var p = nearP(%s, 'Position'); return (p ? 'P' + p + '  ' : '') + '#' + nz(nearP(%s, 'CarNumber'), '');"
              % (on, k, k),
              samples[0], size=20, weight="SemiBold", color=LABEL, name=title + " pos", refresh=250),
        # name (white), then iRating and licence / SR in the licence colour, same font
        value(x + 24, y + 42, 218, 44, "return %s ? shortName(nearP(%s, 'Name'), 13) : '—';" % (on, k),
              samples[1], size=28, weight="SemiBold", name=title + " driver", refresh=500),
        value(x + 246, y + 42, 70, 44, "return %s ? irStr(nearIR(%s)) : '';" % (on, k),
              samples[5], size=28, weight="SemiBold", align="r", name=title + " iR", refresh=2000,
              color_js="var ir = parseFloat(nearIR(%s)); return (ir > 0 && ir < %d) ? '%s' : licTextCol(nearLic(%s));" % (k, LOW_IR, R_, k),
              sample_color=BAD if int(samples[5]) < LOW_IR else samples[7]),
        value(x + 328, y + 42, 96, 44, "return %s ? licText(nearLic(%s)) : '';" % (on, k),
              samples[6], size=28, weight="SemiBold", name=title + " SR", refresh=2000,
              color_js="return licTextCol(nearLic(%s));" % k, sample_color=samples[7]),
        value(x + w - 184, y + 38, 160, 52, "var g = %s ? nearGap(%s) : null; return g === null ? '' : g.toFixed(3);" % (on, k),
              samples[2], size=46, align="r", name=title + " gap", refresh=100),
        # what they drive
        value(x + 24, y + 94, w - 48, 30, "return %s ? nearCar(%s) : '';" % (on, k),
              samples[8], size=20, weight="SemiBold", color=LABEL, name=title + " car", refresh=2000),
        # flashing warning across the whole top line when that driver's iR is low
        Rect(x + 14, y + 10, w - 28, 28, fill=BAD, radius=6, name=title + " low iR banner", visible=False,
             bind={"Visible": JS(low + " && blinkOn(500);")}, refresh=100, sample={"visible": low_sample}),
        Text(x + 14, y + 10, w - 28, 28, "⚠  LOW iRATING", size=20, weight="Bold", color=TEXT, align="c",
             name=title + " low iR text", visible=False,
             bind={"Visible": JS(low + " && blinkOn(500);")}, refresh=100, sample={"visible": low_sample}),
    ]


def build():
    items = chrome_top()

    # ---------------- left column ----------------
    # lap timing, Porsche 911 GT3 R style: big laptime, last lap and predicted below
    best = "myBest()"
    half = (LW - 10) // 2
    items += head_box(LX, TOP, LW, 170, "LAPTIME", "Laptime box")
    items.append(value(LX, TOP + 34, LW, 134, "return lapStr(TN('LapCurrentLapTime', 0));", "1:02.418",
                       size=100, align="c", name="Current lap"))
    items += head_box(LX, 226, half, 140, "LAST LAP", "Last lap box")
    items.append(value(LX, 260, half, 104, "return lapStr(TN('LapLastLapTime', 0));", "1:41.902", size=58, align="c",
                       color_js="var l = TN('LapLastLapTime', 0), b = %s; if (!(l > 0) || !(b > 0)) { return '%s'; }"
                                " if (Math.abs(l - b) < 0.0005) { return '%s'; } return l > b * 1.01 ? '%s' : '%s';"
                                % (best, T_, G, W_, T_),
                       sample_color=TEXT, refresh=250, name="Last lap"))
    items += head_box(LX + half + 10, 226, half, 140, "PRED. TIME", "Predicted box")
    # always green: easiest to read
    items.append(value(LX + half + 10, 260, half, 104, "return lapStr(predicted());", "1:41.113", size=58, align="c",
                       color=GOOD, name="Predicted lap"))

    items += gap_box(LX, 376, LW, 141, "ahead", ["P2  #23", "M. Rossi", "1.284", "", GOOD, "3322", "A 3.41", "#4C8DFF",
                                                  "Porsche 992 GT3R"])
    items += gap_box(LX, 527, LW, 141, "behind", ["P4  #7", "L. Norris", "0.642", "", BAD, "1740", "B 2.99", "#3CCB5A",
                                                   "Ferrari 296 GT3"])

    # ---------------- centre column ----------------
    # delta to YOUR session best, on top of the gear
    delta = "var ok = myDeltaOK(), d = ok ? myDelta() : 0;"
    items.append(panel(CX, TOP, CW, 104, "Delta panel", title="Δ YOUR BEST"))
    items.append(value(CX + 24, TOP + 32, 260, 30, "return lapStr(myBest());", "1:41.455", size=26, weight="SemiBold",
                       color=LABEL, refresh=1000, name="Your best"))
    items.append(value(CX + CW - 264, TOP + 6, 240, 60, delta + " return ok ? sgn(d, 3) : '—';", "−0.342",
                       size=50, align="r",
                       color_js=delta + " return d < -0.0005 ? '%s' : (d > 0.0005 ? '%s' : '%s');" % (G, R_, T_),
                       sample_color=GOOD, name="Delta"))
    bx, bw, by, bh = CX + 24, CW - 48, TOP + 68, 24
    mid, hw = bx + bw // 2, bw // 2
    items.append(Rect(bx, by, bw, bh, fill=OFF, radius=6, name="Delta track"))
    # Faster (negative) grows left from the zero line: a full green half with
    # a track-coloured mask whose width shrinks. Slower grows right in red.
    # Only Width bindings are used, which every SimHub build supports.
    neg = delta + " var w = d < 0 ? Math.min(-d, 2) / 2 * %d : 0;" % hw
    pos = delta + " var w = d > 0 ? Math.min(d, 2) / 2 * %d : 0;" % hw
    sample_w = round(0.342 / 2 * hw)
    items.append(Rect(mid - hw, by, hw, bh, fill=GOOD, radius=0, name="Delta faster",
                      bind={"Visible": JS(delta + " return d < 0;")}))
    items.append(Rect(mid - hw, by, hw - sample_w, bh, fill=OFF, radius=0, name="Delta faster mask",
                      bind={"Width": JS(neg + " return %d - w;" % hw)}))
    items.append(Rect(mid, by, 0, bh, fill=BAD, radius=0, name="Delta slower",
                      bind={"Width": JS(pos + " return w;")}, sample={"visible": False}))
    items.append(Rect(mid - 1, by - 5, 2, bh + 10, fill=TEXT, name="Delta zero"))

    gear_bg = FLASH + " return fl ? (red ? '%s' : '%s') : '%s';" % (R_, W_, argb(BG))
    items.append(Rect(CX, 160, CW, BOT - 160, fill=BG, stroke=BORDER, stroke_w=2, radius=18,
                      name="Gear panel", bind={"BackgroundColor": JS(gear_bg)}))
    items.append(Text(CX + 110, 164, CW - 220, BOT - 168, "4", size=440, weight="Bold", color=TEXT, align="c", name="Gear",
                      bind={"Text": NC("isnull([Gear], 'N')"), "TextColor": JS(on_gear_panel(TEXT))},
                      sample={"text": "4"}))

    # ---------------- right column: car settings, fuel, session ----------------
    cells = [   # top-left, top-right, bottom-left, bottom-right
        ("MAP", "return fx(N('EngineMap', null), 0);", "2"),
        ("TC", "return fx(N('TCLevel', null), 0);", "3"),
        ("BB", "return fx(N('BrakeBias', null), 1);", "54.2"),
        ("ABS", "return fx(N('ABSLevel', null), 0);", "4"),
    ]
    cw = (RW - 10) // 2
    for i, (name, js, sample) in enumerate(cells):
        x, y = RX + (i % 2) * (cw + 10), TOP + (i // 2) * 94
        # coloured box, title in the outline, value in the same colour
        items.append(panel(x, y, cw, 84, name + " panel", title=name, accent=ACCENTS[name]))
        if name == "BB":
            # when you change brake bias the box fills with its colour and fades back over 2 s
            r, g, b = (int(ACCENTS["BB"][i:i + 2], 16) for i in (1, 3, 5))
            items.append(Rect(x + 3, y + 3, cw - 6, 78, fill="#00FFFFFF", radius=15, name="BB change highlight",
                              bind={"BackgroundColor": JS("return '#' + hex2(bbFade() * 230) + '%s';" % ACCENTS["BB"][1:].upper())}))
            # number: white on the fill, fading back to the box colour
            fade_col = ("var p = bbFade(), w = [242, 244, 247], c = [%d, %d, %d];"
                        " return '#FF' + hex2(c[0] + (w[0] - c[0]) * p) + hex2(c[1] + (w[1] - c[1]) * p) + hex2(c[2] + (w[2] - c[2]) * p);"
                        % (r, g, b))
            items.append(value(x, y + 2, cw, 82, js, sample, size=58, align="c", color=ACCENTS[name],
                               color_js=fade_col, name=name))
        else:
            items.append(value(x, y + 2, cw, 82, js, sample, size=58, align="c", color=ACCENTS[name],
                               refresh=200, name=name))

    items.append(panel(RX, 234, RW, 150, "Fuel panel", title="FUEL"))
    fuel_cells = [
        ("PER LAP", "return fx(fuelData().per, 2);", "2.61", None, None),
        ("FUEL LAPS", "return fx(fuelData().lof, 1);", "14.7",
         "var f = fuelData(); return (f.lof !== null && f.lof < 2) ? '%s' : '%s';" % (R_, T_), None),
        ("LAST LAP", "return fx(fuelData().last, 2);", "2.58", None, None),
        ("TO FINISH", "var a = fuelData().add; return (a === null || a === undefined) ? '—' : sgn(a, 1) + ' L';", "+6.2 L",
         "var a = fuelData().add; return (a === null || a === undefined) ? '%s' : (a > 0 ? '%s' : '%s');" % (T_, R_, G), BAD),
    ]
    for k, (name, js, sample, cjs, scol) in enumerate(fuel_cells):
        items += stat(RX + 24 + k * 146, 262, 138, name, js, sample, vsize=44, color_js=cjs, sample_color=scol, refresh=250)

    items.append(panel(RX, 394, RW, BOT - 394, "Session panel", title="SESSION"))
    col = [RX + 24, RX + 220, RX + 416]
    top, bot = 416, 540
    # top row: fuel left, iR estimate, strength of field
    items += stat(col[0], top, 180, "FUEL LEFT", "var f = fuelData(); return fx(f.fuel, 1) + ' L';", "38.4 L", vsize=52, refresh=250,
                  color_js="var f = fuelData(); return (f.lof !== null && f.lof !== undefined && f.lof < 2) ? '%s' : '%s';" % (R_, T_))
    items += stat(col[1], top, 180, "iR EST.", "var v = XN('Player_iRGainEstimation', null); return v === null ? '—' : sgn(v, 0);",
                  "+24", vsize=52, refresh=1000,
                  color_js="var v = XN('Player_iRGainEstimation', 0); return v > 0 ? '%s' : (v < 0 ? '%s' : '%s');" % (G, R_, T_),
                  sample_color=GOOD)
    items += stat(col[2], top, 176, "SOF", "return fx(sofCalc(), 0);", "2314", vsize=52, refresh=5000)
    # bottom row: laps left, time left, incidents
    items += stat(col[0], bot, 180, "LAPS LEFT", "var l = lapsLeft(); return l === null ? '—' : '' + l;",
                  "19", vsize=52, refresh=500)
    items += stat(col[1], bot, 180, "TIME LEFT", "var t = timeLeft(); return t === null ? '—' : clockStr(t);",
                  "23:14", vsize=52, refresh=500)
    items += stat(col[2], bot, 176, "INCIDENTS", "var i = incidents(); return fx(i.n, 0) + 'x';", "4x", vsize=52, refresh=500,
                  color_js="var i = incidents(); return (i.limit !== null && i.n >= i.limit - 4) ? '%s' : '%s';" % (R_, T_))
    items.append(value(col[2] + 76, bot + 50, 100, 24, "var i = incidents(); return i.limit === null ? '' : '/ ' + i.limit;",
                       "/ 17", size=20, weight="SemiBold", color=LABEL, align="r", refresh=1000, name="Incident limit"))

    items += chrome_bottom("RACE")
    return Screen("RACE", items)
