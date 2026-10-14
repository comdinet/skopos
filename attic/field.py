"""FIELD: every driver in the session sorted by car number, with licence /
safety rating and iRating. Up to 51 cars in three balanced columns (1920x720).

Also shown automatically (as an overlay) while you are in the garage, i.e. not
in the car on track."""

import math

from ..dsl import JS, Rect, Screen, Text, repeated
from ..theme import (GARAGE_PAGES, ACCENT, ACCENT_BG, LABEL, PANEL_HI, TEXT, argb)
from .common import chrome_bottom, chrome_top, label, panel, value

COLS = 3
COL_W, COL_GAP = 540, 20
X0 = (1920 - (COLS * COL_W + (COLS - 1) * COL_GAP)) // 2   # block centred on screen
COL_X = [X0 + k * (COL_W + COL_GAP) for k in range(COLS)]
X1 = COL_X[-1] + COL_W
ROWS = 17
ROW_Y, ROW_H = 120, 31

SURNAMES = ["Alvarez", "Becker", "Costa", "Dubois", "Eriksen", "Fischer", "Garcia", "Horvat", "Ivanov", "Jensen",
            "Kowalski", "Laine", "Moreau", "Novak", "Ortega", "Petrov", "Quinn", "Rossi", "Silva", "Tanaka",
            "Ueda", "Varga", "Weber", "Xu", "Young", "Zeller", "Andersen", "Bianchi", "Carter", "Dijkstra",
            "Esposito", "Fontaine", "Grant", "Hughes", "Ito", "Janssen", "Keller", "Lopez", "Meyer", "Nowak",
            "Olsen", "Park", "Reyes", "Schmidt", "Torres", "Vogel"]
LICS = ["A 3.41", "B 2.87", "C 3.10", "A 4.12", "B 3.66", "D 2.41", "A 2.99", "C 2.54", "B 3.95", "R 2.10", "A 4.99"]
NUMS = sorted({(i * 37) % 99 + 1 for i in range(1, 60)})[:46]


def sample_field():
    rows = []
    for k, num in enumerate(NUMS):
        name = "%s. %s" % ("ABCDEFGHJKLMNPRST"[k % 17], SURNAMES[k])
        ir = 1200 + (k * 397) % 3400
        rows.append({"num": str(num), "name": name, "lic": LICS[k % len(LICS)], "ir": str(ir),
                     "pos": "P%d" % ((k * 17) % 46 + 1), "player": num == 44 or (k == 20 and 44 not in NUMS),
                     "pit": k in (7, 31)})
    return rows


LIC_BG = {"R": "#D93A2B", "D": "#F08A24", "C": "#F2C230", "B": "#3CB04E", "A": "#2F6FE4", "P": "#0B0E12"}
LIC_FG = {"D": "#0B0E12", "C": "#0B0E12", "B": "#0B0E12"}


def column(col, samples):
    px = COL_X[col]
    slot = ("var n = fieldSlots().length, rpc = Math.max(1, Math.ceil(n / %d)), i = repeatindex();"
            " var s = i > rpc ? 0 : fieldSlot(%d * rpc + i);" % (COLS, col))

    def row(s):
        y = ROW_Y
        player = s.get("player", False)
        lic = s["lic"]
        return [
            Rect(px + 6, y, COL_W - 12, ROW_H - 3, fill=PANEL_HI, radius=5, name="Row bg",
                 bind={"BackgroundColor": JS(slot + " if (s > 0 && s === playerSlot()) { return '%s'; } return repeatindex() %% 2 === 0 ? '%s' : '#00FFFFFF';"
                                             % (argb(ACCENT_BG), argb(PANEL_HI))),
                       "Visible": JS(slot + " return s > 0;")},
                 refresh=1000, sample={"fill": ACCENT_BG if player else PANEL_HI}),
            Rect(px + 12, y + 3, 60, ROW_H - 9, fill="#FFDA59", radius=4, name="Number chip",
                 bind={"BackgroundColor": JS(slot + " return clsColor(drv(s, 'CarClassColor'));"),
                       "Visible": JS(slot + " return s > 0;")}, refresh=2000),
            Text(px + 12, y + 3, 60, ROW_H - 9, s["num"], size=20, weight="Bold", color="#0B0E12", align="c",
                 name="Number", bind={"Text": JS(slot + " return s > 0 ? '' + nz(drv(s, 'CarNumber'), '') : '';")},
                 refresh=1000, sample={"text": s["num"]}),
            Text(px + 80, y, 200, ROW_H - 3, s["name"], size=22, weight="SemiBold", color=TEXT, name="Name",
                 bind={"Text": JS(slot + " return s > 0 ? shortName(drv(s, 'UserName'), 16) : '';"),
                       "TextColor": JS(slot + " return (s > 0 && s === playerSlot()) ? '%s' : '%s';"
                                       % (argb(ACCENT), argb(TEXT)))},
                 refresh=1000, sample={"text": s["name"], "color": ACCENT if player else TEXT}),
            Rect(px + 286, y + 3, 96, ROW_H - 9, fill=LIC_BG[lic[0]], radius=4, name="Licence badge",
                 bind={"BackgroundColor": JS(slot + " return licBg(drv(s, 'LicString'));"),
                       "Visible": JS(slot + " return s > 0;")}, refresh=2000),
            Text(px + 286, y + 3, 96, ROW_H - 9, lic, size=18, weight="Bold", color=LIC_FG.get(lic[0], "#F2F4F7"),
                 align="c", name="Licence",
                 bind={"Text": JS(slot + " return s > 0 ? licText(drv(s, 'LicString')) : '';"),
                       "TextColor": JS(slot + " return licFg(drv(s, 'LicString'));")},
                 refresh=2000, sample={"text": lic}),
            Text(px + 388, y, 66, ROW_H - 3, s["ir"], size=20, weight="SemiBold", color=TEXT, align="r", name="iRating",
                 bind={"Text": JS(slot + " return s > 0 ? irStr(drv(s, 'IRating')) : '';")},
                 refresh=2000, sample={"text": s["ir"]}),
            Text(px + 462, y, 64, ROW_H - 3, "PIT" if s.get("pit") else s["pos"], size=20, weight="SemiBold",
                 color=ACCENT if s.get("pit") else LABEL, align="r", name="Position",
                 bind={"Text": JS(slot + " if (s <= 0) { return ''; } var ci = +drv(s, 'CarIdx');"
                                  " if (arrAt('CarIdxOnPitRoad', ci) === true) { return 'PIT'; }"
                                  " var p = arrAt('CarIdxPosition', ci); return p > 0 ? 'P' + p : '';"),
                       "TextColor": JS(slot + " var ci = +drv(s, 'CarIdx'); return arrAt('CarIdxOnPitRoad', ci) === true ? '%s' : '%s';"
                                       % (argb(ACCENT), argb(LABEL)))},
                 refresh=1000, sample={"text": "PIT" if s.get("pit") else s["pos"],
                                       "color": ACCENT if s.get("pit") else LABEL}),
        ]

    items = [panel(px, 86, COL_W, 578, "Column %d" % (col + 1))]
    for x, w, t, a in ((px + 12, 60, "#", "c"), (px + 80, 200, "DRIVER", "l"), (px + 286, 96, "LIC / SR", "c"),
                       (px + 388, 66, "iR", "r"), (px + 462, 64, "POS", "r")):
        items.append(label(x, 92, w, t, align=a, size=18, h=24))
    items.append(repeated(ROWS, ROW_H, row, samples, "Field column %d" % (col + 1)))
    return items


def _items(title_extra="", garage=False):
    items = chrome_top(0)
    field = sample_field()
    rpc = math.ceil(len(field) / COLS)
    items.append(Text(X0 + 8, 46, 130, 36, "FIELD", size=28, weight="Bold", color=TEXT, name="Title"))
    items.append(value(X0 + 138, 46, 700, 36, "return fieldSlots().length + ' cars  \u00b7  sorted by car number%s';" % title_extra,
                       "%d cars  \u00b7  sorted by car number%s" % (len(field), title_extra), size=20, weight="SemiBold",
                       color=LABEL, refresh=2000, name="Count"))
    items.append(value(X1 - 708, 46, 700, 36,
                       "var sof = sofCalc(); var me = drv(playerSlot(), 'CarNumber');"
                       " return (me ? 'you #' + me + '   \u00b7   ' : '') + 'SoF ' + (sof ? sof : '\u2014');",
                       "you #44   \u00b7   SoF 2314", size=20, weight="SemiBold", color=LABEL, align="r",
                       refresh=5000, name="SoF"))
    for col in range(COLS):
        items += column(col, field[col * rpc:(col + 1) * rpc])
    items += chrome_bottom("FIELD", GARAGE_PAGES if garage else None)
    return items


def build():
    return Screen("FIELD", _items())


def build_garage():
    """Garage copy: while you are in the garage only this and the garage Timing
    page are enabled, so next/previous switches between the two."""
    return Screen("FIELD (garage)", _items("  \u00b7  garage", garage=True))
