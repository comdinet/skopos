"""FIELD (garage only, multi-class sessions only): one column per class with
the class SoF and car count in its header, then the drivers in class-position
order with iR and licence / SR. Shows up to 3 classes (fastest class first).

Purpose: see how strong the other classes are before the race -- iRacing can
put a 1k-SoF GTP class into the top GT3 split.
"""

from ..dsl import JS, Rect, Screen, Text, repeated
from ..theme import (ACCENT, ACCENT_BG, GARAGE_PAGES, LABEL, PANEL_HI, TEXT, argb)
from .common import chrome_bottom, label, panel, value

COLS = 3
COL_W = 628
COL_X = [8 + k * (COL_W + 10) for k in range(COLS)]
ROWS = 19
ROW_Y, ROW_H = 108, 29

LIC_BG = {"R": "#D93A2B", "D": "#F08A24", "C": "#F2C230", "B": "#3CB04E", "A": "#2F6FE4", "P": "#0B0E12"}
LIC_FG = {"D": "#0B0E12", "C": "#0B0E12", "B": "#0B0E12"}

# mockup data: a weak GTP class in a strong GT3 split
SAMPLE = [
    ("GTP", "#E6E8EB", 1184, 8, ["J. Ortega", "R. Silva", "T. Becker", "N. Jensen", "F. Moreau", "H. Park", "S. Laine", "E. Novak"],
     [1450, 980, 1320, 870, 1510, 1120, 760, 1390], ["C 2.41", "D 3.10", "C 1.95", "R 2.80", "B 2.66", "D 1.87", "R 3.02", "C 2.20"]),
    ("LMP2", "#3DA5FF", 1862, 10, ["K. Tanaka", "A. Costa", "D. Weber", "M. Horvat", "P. Novak", "L. Garcia", "B. Keller", "C. Ito", "E. Lopez", "G. Meyer"],
     [2210, 1950, 1740, 2060, 1680, 1890, 1720, 1540, 2380, 1610], ["B 3.20", "B 2.95", "C 3.41", "A 2.77", "C 2.60", "B 3.66", "C 2.88", "D 3.10", "A 3.05", "C 2.45"]),
    ("GT3", "#FFDA59", 3121, 22, ["A. Kowalski", "M. Rossi", "You", "L. Norris", "E. Dubois", "F. Fischer", "I. Ivanov", "Q. Quinn",
                                  "S. Schmidt", "T. Torres", "V. Vogel", "O. Olsen", "R. Reyes", "Y. Young", "Z. Zeller", "U. Ueda"],
     [4210, 3322, 2931, 1740, 3890, 3450, 2980, 3120, 2760, 3310, 2890, 3040, 2650, 3580, 2810, 2990],
     ["A 4.12", "A 3.41", "A 3.87", "B 2.99", "A 4.55", "A 3.20", "B 3.66", "A 2.87", "B 3.14", "A 3.95", "B 2.70", "A 3.33", "B 3.01", "A 4.02", "B 2.94", "A 3.48"]),
]


def column(k):
    px = COL_X[k]
    C = "var c = classes()[%d];" % k
    has = C + " return !!c;"
    name, col, sof, n, names, irs, lics = SAMPLE[k]
    items = [
        panel(px, 14, COL_W, 654, "Class %d panel" % (k + 1), bind={"Visible": JS(has)}, refresh=2000),
        # class header: name chip in the class colour, SoF, car count
        Rect(px + 16, 28, 150, 40, fill=col, radius=8, name="Class %d chip" % (k + 1),
             bind={"BackgroundColor": JS(C + " return c ? c.color : '#00FFFFFF';"), "Visible": JS(has)}, refresh=2000),
        Text(px + 16, 28, 150, 40, name, size=24, weight="Bold", color="#0B0E12", align="c", name="Class %d name" % (k + 1),
             bind={"Text": JS(C + " return c ? shortName(c.name, 10) : '';"), "Visible": JS(has)}, refresh=2000,
             sample={"text": name}),
        value(px + 180, 24, 260, 48, C + " return c && c.sof > 0 ? 'SoF ' + c.sof : '';", "SoF %d" % sof,
              size=36, name="Class %d SoF" % (k + 1), refresh=2000),
        value(px + 452, 24, 160, 48, C + " return c ? c.n + ' cars' : '';", "%d cars" % n, size=22,
              weight="SemiBold", color=LABEL, align="r", name="Class %d count" % (k + 1), refresh=2000),
    ]
    for x, w, t, a in ((px + 12, 48, "POS", "c"), (px + 66, 60, "#", "c"), (px + 136, 250, "DRIVER", "l"),
                       (px + 390, 66, "iR", "r"), (px + 470, 110, "LIC / SR", "c")):
        items.append(label(x, 78, w, t, align=a, size=18, h=24))

    slot = C + " var i = repeatindex(), s = (c && i <= c.slots.length) ? +c.slots[i - 1] : 0;"
    rows = []
    for i in range(min(len(names), ROWS)):
        rows.append({"pos": "P%d" % (i + 1), "num": str(3 + i * 7 + k * 20), "name": names[i], "ir": str(irs[i]),
                     "lic": lics[i], "player": names[i] == "You", "color": col})

    def row(s):
        y = ROW_Y
        lic = s["lic"]
        return [
            Rect(px + 6, y, COL_W - 12, ROW_H - 3, fill=PANEL_HI, radius=5, name="Row bg",
                 bind={"BackgroundColor": JS(slot + " if (s > 0 && s === playerSlot()) { return '%s'; } return i %% 2 === 0 ? '%s' : '#00FFFFFF';"
                                             % (argb(ACCENT_BG), argb(PANEL_HI))),
                       "Visible": JS(slot + " return s > 0;")},
                 refresh=2000, sample={"fill": ACCENT_BG if s["player"] else PANEL_HI}),
            Text(px + 12, y, 48, ROW_H - 3, s["pos"], size=18, weight="SemiBold", color=LABEL, align="c", name="Class pos",
                 bind={"Text": JS(slot + " var p = (c && s > 0) ? c.pos[i - 1] : 0; return p > 0 ? 'P' + p : (s > 0 ? '\\u2014' : '');")},
                 refresh=2000, sample={"text": s["pos"]}),
            Rect(px + 66, y + 3, 60, ROW_H - 9, fill=s["color"], radius=4, name="Number chip",
                 bind={"BackgroundColor": JS(C + " return c ? c.color : '#00FFFFFF';"), "Visible": JS(slot + " return s > 0;")},
                 refresh=2000),
            Text(px + 66, y + 3, 60, ROW_H - 9, s["num"], size=18, weight="Bold", color="#0B0E12", align="c", name="Number",
                 bind={"Text": JS(slot + " return s > 0 ? '' + nz(drv(s, 'CarNumber'), '') : '';")}, refresh=2000,
                 sample={"text": s["num"]}),
            Text(px + 136, y, 250, ROW_H - 3, s["name"], size=20, weight="SemiBold", color=TEXT, name="Name",
                 bind={"Text": JS(slot + " return s > 0 ? shortName(drv(s, 'UserName'), 20) : '';"),
                       "TextColor": JS(slot + " return (s > 0 && s === playerSlot()) ? '%s' : '%s';" % (argb(ACCENT), argb(TEXT)))},
                 refresh=2000, sample={"text": s["name"], "color": ACCENT if s["player"] else TEXT}),
            Text(px + 390, y, 66, ROW_H - 3, s["ir"], size=20, weight="SemiBold", color=TEXT, align="r", name="iRating",
                 bind={"Text": JS(slot + " return s > 0 ? irStr(drv(s, 'IRating')) : '';")}, refresh=2000,
                 sample={"text": s["ir"]}),
            Rect(px + 470, y + 3, 110, ROW_H - 9, fill=LIC_BG[lic[0]], radius=4, name="Licence badge",
                 bind={"BackgroundColor": JS(slot + " return licBg(drv(s, 'LicString'));"), "Visible": JS(slot + " return s > 0;")},
                 refresh=2000),
            Text(px + 470, y + 3, 110, ROW_H - 9, lic, size=18, weight="Bold", color=LIC_FG.get(lic[0], "#F2F4F7"),
                 align="c", name="Licence",
                 bind={"Text": JS(slot + " return s > 0 ? licText(drv(s, 'LicString')) : '';"),
                       "TextColor": JS(slot + " return licFg(drv(s, 'LicString'));")},
                 refresh=2000, sample={"text": lic}),
        ]

    items.append(repeated(ROWS, ROW_H, row, rows, "Class %d rows" % (k + 1)))
    return items


def build_garage():
    items = []
    for k in range(COLS):
        items += column(k)
    items += chrome_bottom("FIELD", GARAGE_PAGES)
    # summary in the footer, between the page tabs and the session clock
    items.append(value(620, 678, 600, 36,
                       "var c = classes(), t = 0; for (var k = 0; k < c.length; k++) { t += c[k].n; }"
                       " return c.length + ' classes  \u00b7  ' + t + ' cars' + (c.length > 3 ? '  \u00b7  first 3 classes shown' : '');",
                       "3 classes  \u00b7  40 cars", size=20, weight="SemiBold", color=LABEL, refresh=2000, name="Summary"))
    return Screen("FIELD (garage)", items)
