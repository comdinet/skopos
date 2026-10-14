"""Chrome shared by every in-game page: shift lights, flag frame, footer tabs."""

from ..dsl import JS, Group, Rect, Text
from ..theme import (ACCENT, BAD, BG, GOOD, LABEL, LINE, OFF, PAGES, PANEL, TEXT, WARN, argb)

LED_N = 20
LED_RED = argb(BAD)
LED_YELLOW = argb(WARN)
LED_OFF = argb(OFF)
SHIFT_BLINK_MS = 110


def led_color(i):
    if i <= 7:
        return GOOD
    if i <= 14:
        return WARN
    return BAD


# Panel look. "flat": filled grey cards (current dash). "bordered": black boxes
# with a light outline and the section title set into the top line, like the
# user's reference dashboards. Switched by build.py for the proposal mockup.
STYLE = {"mode": "bordered"}
BORDER = "#E6E8EB"
ACCENTS = {"TC": "#3DD6F5", "ABS": "#FFC53D", "BB": "#FF4D4D", "MAP": "#2BD46B"}


def bordered():
    return STYLE["mode"] == "bordered"


def panel(x, y, w, h, name="Panel", fill=PANEL, title=None, accent=None, **kw):
    if not bordered():
        return Rect(x, y, w, h, fill=fill, stroke=LINE, stroke_w=1, radius=12, name=name, **kw)
    col = accent or BORDER
    box = Rect(x, y, w, h, fill=BG, stroke=col, stroke_w=2, radius=18, name=name, **kw)
    if not title:
        return box
    tw = int(len(title) * 11 + 28)
    cut = Text(x + (w - tw) / 2.0, y - 10, tw, 22, title, size=18, weight="Bold",
               color=accent or TEXT, align="c", bg=BG, name=name + " title")
    return Group([box, cut], name=name)


HEAD = "#2B313A"   # header strip of the Porsche-style timing boxes


def head_box(x, y, w, h, title, name):
    """Outlined box with a filled header strip carrying its label (like the
    Porsche 911 GT3 R display). Returns the items; put the value below y+32."""
    r = 14
    return [
        Rect(x, y, w, h, fill=BG, stroke=BORDER, stroke_w=2, radius=r, name=name),
        Rect(x + 2, y + 2, w - 4, 30, fill=HEAD, corners=(r - 2, r - 2, 0, 0), name=name + " header"),
        Text(x + 16, y + 2, w - 32, 30, title, size=18, weight="Bold", color=TEXT, align="c", name=name + " label"),
    ]


def ptitle(x, y, w, text, **kw):
    """Top-left section label in the flat look; the bordered look carries the
    title in the panel outline instead."""
    return [] if bordered() else [label(x, y, w, text, **kw)]


def label(x, y, w, text, align="l", size=20, color=LABEL, h=28, name=None):
    return Text(x, y, w, h, text, size=size, color=color, weight="SemiBold", align=align,
                name=name or ("Label " + text))


def value(x, y, w, h, js, sample, size=56, color=TEXT, align="l", weight="Bold",
          refresh=0, color_js=None, sample_color=None, name="Value", visible_js=None, sample_visible=True):
    bind = {"Text": JS(js)}
    s = {"text": sample}
    if color_js:
        bind["TextColor"] = JS(color_js)
        if sample_color:
            s["color"] = sample_color
    if visible_js:
        bind["Visible"] = JS(visible_js)
        s["visible"] = sample_visible
    return Text(x, y, w, h, sample, size=size, color=color, weight=weight, align=align,
                bind=bind, refresh=refresh, sample=s, name=name)


def stat(x, y, w, title, js, sample, vsize=48, align="l", **kw):
    """Label above a value."""
    return [
        label(x, y, w, title, align=align),
        value(x, y + 30, w, vsize + 12, js, sample, size=vsize, align=align, name=title, **kw),
    ]


def shift_lights(lit=11):
    items = []
    x0, x1, gap, top, h = 8, 1912, 8, 8, 28
    w = (x1 - x0 - gap * (LED_N - 1)) / LED_N
    for i in range(1, LED_N + 1):
        a = round(x0 + (i - 1) * (w + gap))
        b = round(x0 + (i - 1) * (w + gap) + w)
        on = argb(led_color(i))
        # at the shift point every LED alternates red / yellow (never dark)
        js = ("var s = shiftLeds(); if (s >= 99) { return blinkOn(SHIFT_BLINK_MS) ? '%s' : '%s'; } "
              "return s >= %d ? '%s' : '%s';" % (LED_RED, LED_YELLOW, i, on, LED_OFF)).replace(
                  "SHIFT_BLINK_MS", str(SHIFT_BLINK_MS))
        items.append(Rect(a, top, b - a, h, fill=OFF, radius=6, name="LED %d" % i,
                          bind={"BackgroundColor": JS(js)},
                          sample={"fill": led_color(i) if i <= lit else OFF}))
    return items


FLAG_JS = """function flagInfo() {
  if (B('Flag_Checkered')) { return ['CHECKERED', '#FFF2F4F7', '#FF0B0E12']; }
  if (B('Flag_Black')) { return ['BLACK FLAG', '#FFFF4D4D', '#FF0B0E12']; }
  if (B('Flag_Orange')) { return ['REPAIR', '#FFFF8A1F', '#FF0B0E12']; }
  if (B('Flag_Yellow')) { return ['YELLOW', '#FFFFC53D', '#FF0B0E12']; }
  if (B('Flag_Blue')) { return ['BLUE FLAG', '#FF3DA5FF', '#FF0B0E12']; }
  if (B('Flag_White')) { return ['LAST LAP', '#FFF2F4F7', '#FF0B0E12']; }
  return null;
}
"""


def flag_frame():
    vis = FLAG_JS + "return flagInfo() !== null;"
    col = FLAG_JS + "var f = flagInfo(); return f ? f[1] : '#00FFFFFF';"
    edges = [(0, 0, 1920, 6), (0, 714, 1920, 6), (0, 0, 6, 720), (1914, 0, 6, 720)]
    return [Rect(x, y, w, h, fill="#00FFFFFF", name="Flag frame", visible=False,
                 bind={"Visible": JS(vis), "BackgroundColor": JS(col)}, refresh=100,
                 sample={"visible": False})
            for (x, y, w, h) in edges]


def footer(active, pages=None):
    items = [
        Rect(0, 676, 1920, 44, fill="#0A0D11", name="Footer"),
        Rect(0, 676, 1920, 1, fill=LINE, name="Footer line"),
    ]
    for idx, name in enumerate(pages or PAGES):
        x = 16 + idx * 144
        on = name == active
        tab_bind = {"Visible": JS("return classCount() >= 2;")} if name == "FIELD" else None
        items.append(Text(x, 678, 136, 34, name, size=20, weight="SemiBold",
                          color=TEXT if on else LABEL, align="c", name="Tab " + name, bind=tab_bind,
                          refresh=2000 if tab_bind else 0))
        if on:
            items.append(Rect(x + 28, 709, 80, 3, fill=ACCENT, radius=1, name="Tab marker"))
    # flag chip
    items.append(Rect(1236, 682, 180, 32, fill=WARN, radius=6, name="Flag chip", visible=False,
                      bind={"Visible": JS(FLAG_JS + "return flagInfo() !== null;"),
                            "BackgroundColor": JS(FLAG_JS + "var f = flagInfo(); return f ? f[1] : '#00FFFFFF';")},
                      refresh=100, sample={"visible": False}))
    items.append(Text(1236, 682, 180, 32, "YELLOW", size=18, weight="Bold", color="#0B0E12", align="c",
                      name="Flag text", visible=False, refresh=100, sample={"visible": False},
                      bind={"Visible": JS(FLAG_JS + "return flagInfo() !== null;"),
                            "Text": JS(FLAG_JS + "var f = flagInfo(); return f ? f[0] : '';")}))
    items.append(value(1440, 678, 300, 36,
                       "var t = timeLeft(), s = ('' + P('SessionTypeName', '')).toUpperCase();"
                       " return s + (t !== null ? '   ' + clockStr(t) : '');",
                       "RACE   23:14", size=20, weight="SemiBold", color=LABEL, align="r",
                       refresh=500, name="Session"))
    items.append(value(1764, 678, 140, 36,
                       "var d = new Date(); return pad2(d.getHours()) + ':' + pad2(d.getMinutes());",
                       "21:42", size=24, weight="Bold", align="r", refresh=1000, name="Clock"))
    return items


def chrome_top(lit=11):
    return shift_lights(lit)


def chrome_bottom(active, pages=None):
    # flags only as a small chip in the footer (no screen border)
    return footer(active, pages)
