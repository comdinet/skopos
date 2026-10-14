"""TIMING: the whole field in one column in the middle of the screen, for when
you join a session and during / after qualifying. Cars with a lap time come
first, fastest first; cars without a time follow, highest iRating first.
Holds 24 drivers; with more, the top 12 and the bottom 12 are shown and the
middle is hidden (marked by a line, count in the footer). No shift lights.
"""

from ..dsl import JS, Rect, Screen, Text, repeated
from ..theme import (ACCENT, ACCENT_BG, GARAGE_PAGES, LABEL, PANEL_HI, PURPLE, TEXT, argb)
from .common import chrome_bottom, label, panel, value

ROWS, SPLIT = 24, 12            # 24 rows; above that: first 12 + last 12
TW = 1200                       # table width, centred
TX = (1920 - TW) // 2
ROW_Y, ROW_H = 48, 25

LIC_BG = {"R": "#D93A2B", "D": "#F08A24", "C": "#F2C230", "B": "#3CB04E", "A": "#2F6FE4", "P": "#0B0E12"}
LIC_FG = {"D": "#0B0E12", "C": "#0B0E12", "B": "#0B0E12"}

SURNAMES = ["Kowalski", "Rossi", "You", "Norris", "Tanaka", "Ortega", "Novak", "Park", "Laine", "Jensen", "Moreau",
            "Becker", "Silva", "Weber", "Costa", "Dubois", "Eriksen", "Fischer", "Garcia", "Horvat", "Ivanov",
            "Keller", "Lopez", "Meyer", "Nowak", "Olsen", "Petrov", "Quinn", "Reyes", "Schmidt"]
CARS = ["Porsche 992 GT3R", "Ferrari 296 GT3", "BMW M4 GT3", "Mercedes-AMG GT3", "McLaren 720S GT3 EVO",
        "Audi R8 LMS EVO II", "Lamborghini Huracan GT3 EVO", "Ford Mustang GT3", "Aston Martin Vantage GT3"]

# which field index each row shows (1-based); rows past SPLIT show the tail of the field
IDX = ("var ft = fieldTiming(), n = ft.length, i = repeatindex(),"
       " k = (n <= %d || i <= %d) ? i : n - %d + i, r = k <= n ? ft[k - 1] : null, s = r ? +r[0] : 0;"
       % (ROWS, SPLIT, ROWS))


def sample_rows():
    rows, fastest = [], 101.022
    for k, sur in enumerate(SURNAMES):
        timed = k < 15
        best = fastest + k * 0.137 + (k * k) * 0.006 if timed else 0
        ir = 4210 - k * 90 if timed else 3950 - (k - 15) * 260
        lic = ["A 4.12", "A 3.41", "A 3.87", "B 2.99", "B 3.20", "B 3.66", "B 3.95", "C 3.10", "B 3.02", "B 2.77",
               "C 3.44", "C 2.87", "D 2.41", "B 2.54", "A 2.95"][k % 15]
        name = "You" if sur == "You" else "%s. %s" % ("AMLKJEHSNFTRDPC"[k % 15], sur)
        rows.append({"pos": str(k + 1), "num": str((k * 37) % 99 + 1), "name": name, "lic": lic, "ir": str(ir),
                     "best": best, "player": sur == "You", "car": CARS[(k * 5) % len(CARS)]})
    return rows


def lap(s):
    if not s:
        return ""
    m = int(s // 60)
    return "%d:%06.3f" % (m, s - m * 60)


def row(sm, fastest):
    y, px = ROW_Y, TX
    lic, best = sm["lic"], sm["best"]
    gap = "" if not best or best == fastest else "+%.3f" % (best - fastest)
    R = IDX
    return [
        Rect(px + 6, y, TW - 12, ROW_H - 2, fill=PANEL_HI, radius=5, name="Row bg",
             bind={"BackgroundColor": JS(R + " if (s > 0 && s === playerSlot()) { return '%s'; } return i %% 2 === 0 ? '%s' : '#00FFFFFF';"
                                         % (argb(ACCENT_BG), argb(PANEL_HI))),
                   "Visible": JS(R + " return s > 0;")},
             refresh=1000, sample={"fill": ACCENT_BG if sm["player"] else PANEL_HI}),
        Text(px + 14, y, 44, ROW_H - 2, sm["pos"], size=19, weight="SemiBold", color=LABEL, align="c", name="Pos",
             bind={"Text": JS(R + " return s > 0 ? '' + k : '';")}, refresh=1000, sample={"text": sm["pos"]}),
        Rect(px + 64, y + 2, 58, ROW_H - 6, fill="#FFDA59", radius=4, name="Number chip",
             bind={"BackgroundColor": JS(R + " return clsColor(drv(s, 'CarClassColor'));"),
                   "Visible": JS(R + " return s > 0;")}, refresh=2000),
        Text(px + 64, y + 2, 58, ROW_H - 6, sm["num"], size=17, weight="Bold", color="#0B0E12", align="c", name="Number",
             bind={"Text": JS(R + " return s > 0 ? '' + nz(drv(s, 'CarNumber'), '') : '';")}, refresh=2000,
             sample={"text": sm["num"]}),
        Text(px + 132, y, 300, ROW_H - 2, sm["name"], size=20, weight="SemiBold", color=TEXT, name="Name",
             bind={"Text": JS(R + " return s > 0 ? shortName(drv(s, 'UserName'), 24) : '';"),
                   "TextColor": JS(R + " return (s > 0 && s === playerSlot()) ? '%s' : '%s';" % (argb(ACCENT), argb(TEXT)))},
             refresh=2000, sample={"text": sm["name"], "color": ACCENT if sm["player"] else TEXT}),
        Text(px + 442, y, 290, ROW_H - 2, sm["car"], size=18, weight="SemiBold", color=LABEL, name="Car",
             bind={"Text": JS(R + " if (s <= 0) { return ''; } var c = drv(s, 'CarScreenNameShort');"
                              " if (c === null || c === undefined || c === '') { c = drv(s, 'CarScreenName'); } return '' + nz(c, '');")},
             refresh=2000, sample={"text": sm["car"]}),
        Rect(px + 742, y + 2, 96, ROW_H - 6, fill=LIC_BG[lic[0]], radius=4, name="Licence badge",
             bind={"BackgroundColor": JS(R + " return licBg(drv(s, 'LicString'));"), "Visible": JS(R + " return s > 0;")},
             refresh=2000),
        Text(px + 742, y + 2, 96, ROW_H - 6, lic, size=16, weight="Bold", color=LIC_FG.get(lic[0], "#F2F4F7"),
             align="c", name="Licence",
             bind={"Text": JS(R + " return s > 0 ? licText(drv(s, 'LicString')) : '';"),
                   "TextColor": JS(R + " return licFg(drv(s, 'LicString'));")},
             refresh=2000, sample={"text": lic}),
        Text(px + 848, y, 76, ROW_H - 2, sm["ir"], size=20, weight="SemiBold", color=TEXT, align="r", name="iRating",
             bind={"Text": JS(R + " return s > 0 ? irStr(drv(s, 'IRating')) : '';")}, refresh=2000,
             sample={"text": sm["ir"]}),
        Text(px + 940, y, 130, ROW_H - 2, lap(best), size=20, weight="SemiBold", color=TEXT, align="r", name="Best lap",
             bind={"Text": JS(R + " return (r && r[1] > 0) ? lapStr(r[1]) : '';"),
                   "TextColor": JS(R + " return k === 1 ? '%s' : '%s';" % (argb(PURPLE), argb(TEXT)))},
             refresh=1000, sample={"text": lap(best), "color": PURPLE if sm["pos"] == "1" else TEXT}),
        Text(px + 1080, y, 96, ROW_H - 2, gap, size=18, weight="SemiBold", color=LABEL, align="r", name="Gap",
             bind={"Text": JS(R + " var f = n > 0 ? ft[0][1] : 0; return (r && r[1] > 0 && f > 0 && k > 1) ? '+' + (r[1] - f).toFixed(3) : '';")},
             refresh=1000, sample={"text": gap}),
    ]


def build(garage=False):
    rows = sample_rows()
    fastest = rows[0]["best"]
    shown = rows if len(rows) <= ROWS else rows[:SPLIT] + rows[-(ROWS - SPLIT):]
    items = [panel(TX, 14, TW, 654, "Timing panel")]
    for x, w, t, a in ((TX + 14, 44, "POS", "c"), (TX + 64, 58, "#", "c"), (TX + 132, 300, "DRIVER", "l"),
                       (TX + 442, 290, "CAR", "l"), (TX + 742, 96, "LIC / SR", "c"), (TX + 848, 76, "iR", "r"),
                       (TX + 940, 130, "BEST", "r"), (TX + 1080, 96, "GAP", "r")):
        items.append(label(x, 20, w, t, align=a, size=18, h=24))
    items.append(repeated(ROWS, ROW_H, lambda sm: row(sm, fastest), shown, "Timing rows"))
    # line where the middle of a big field is hidden
    items.append(Rect(TX + 14, ROW_Y + SPLIT * ROW_H - 2, TW - 28, 2, fill=ACCENT, name="Hidden marker",
                      bind={"Visible": JS("return fieldTiming().length > %d;" % ROWS)}, refresh=2000,
                      sample={"visible": len(rows) > ROWS}))
    items += chrome_bottom("TIMING", GARAGE_PAGES if garage else None)
    # field summary in the footer, between the page tabs and the session clock
    items.append(value(620, 678, 600, 36,
                       "var ft = fieldTiming(), t = 0; for (var i = 0; i < ft.length; i++) { if (ft[i][1] > 0) { t++; } }"
                       " var sof = sofCalc(), hid = Math.max(0, ft.length - %d);"
                       " return ft.length + ' cars  ·  ' + t + ' with a time' + (hid ? '  ·  ' + hid + ' hidden' : '')"
                       " + (sof ? '  ·  SoF ' + sof : '');" % ROWS,
                       "%d cars  ·  15 with a time  ·  %d hidden  ·  SoF 2314" % (len(rows), len(rows) - ROWS),
                       size=20, weight="SemiBold", color=LABEL, refresh=2000, name="Field summary"))
    return Screen("TIMING (garage)" if garage else "TIMING", items)
