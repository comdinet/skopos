"""Tiny layout DSL that renders to SimHub Dash Studio JSON (.djson) and to
static HTML mockups from the same definitions.

Coordinates are absolute screen pixels (SimHub layers do not offset their
children). Every dynamic element carries a `sample` so the mockup shows
realistic values; the `bind` dict holds the live SimHub formulas.
"""

import html
import uuid

from . import jslib
from .theme import FONT, H, TRANSPARENT, W, argb

NS = "SimHub.Plugins.OutputPlugins.GraphicalDash.Models."
ALIGN_H = {"l": 0, "c": 1, "r": 2}
ALIGN_V = {"t": 0, "c": 1, "b": 2}
CSS_WEIGHT = {"Light": 300, "Normal": 400, "Medium": 500, "SemiBold": 600, "Bold": 700, "Black": 800}


def uid(seed):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "skopos-dash/" + seed))


# --------------------------------------------------------------------------
# Bindings
# --------------------------------------------------------------------------

class JS:
    """JavaScript formula. Helper functions from jslib are inlined on demand."""

    def __init__(self, body):
        self.body = body

    def to_json(self, prop, fmt=None):
        return {
            "Formula": {"Expression": jslib.program(self.body), "Interpreter": 1},
            "Mode": 2,
            "TargetPropertyName": prop,
        }


class NC:
    """NCalc formula (cheaper than JS; used for per-frame hot paths)."""

    def __init__(self, expr):
        self.expr = expr

    def to_json(self, prop, fmt=None):
        out = {"Formula": {"Expression": self.expr}, "Mode": 2, "TargetPropertyName": prop}
        if fmt:
            out["FormatString"] = fmt
        return out


def _bindings(bind):
    if not bind:
        return None
    return {prop: b.to_json(prop) for prop, b in bind.items()}


# --------------------------------------------------------------------------
# Elements
# --------------------------------------------------------------------------

class El:
    def __init__(self, x, y, w, h, name=None, bind=None, refresh=0, sample=None, visible=True):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.name = name or self.__class__.__name__
        self.bind = bind or {}
        self.refresh = refresh
        self.sample = sample or {}
        self.visible = visible

    def shifted(self, dy):
        self.y += dy
        return self

    def _common(self):
        d = {
            "Height": float(self.h),
            "Left": float(self.x),
            "Top": float(self.y),
            "Visible": bool(self.visible),
            "BlinkPhasisInverted": False,
            "Width": float(self.w),
            "Name": self.name,
            "RenderingSkip": 0,
            "MinimumRefreshIntervalMS": float(self.refresh),
        }
        b = _bindings(self.bind)
        if b:
            d["Bindings"] = b
        return d

    def mock_visible(self):
        return self.sample.get("visible", self.visible)


class Rect(El):
    def __init__(self, x, y, w, h, fill="#000000", stroke=None, stroke_w=0, radius=0, corners=None, **kw):
        super().__init__(x, y, w, h, **kw)
        self.fill, self.stroke, self.stroke_w, self.radius = fill, stroke, stroke_w, radius
        # corners = (top-left, top-right, bottom-left, bottom-right) radii
        self.corners = corners or ((radius,) * 4 if radius else None)

    def to_json(self):
        border = {"BorderColor": argb(self.stroke) if self.stroke else TRANSPARENT}
        if self.stroke_w:
            for side in ("Top", "Bottom", "Left", "Right"):
                border["Border" + side] = self.stroke_w
        if self.corners:
            for corner, r in zip(("TopLeft", "TopRight", "BottomLeft", "BottomRight"), self.corners):
                if r:
                    border["Radius" + corner] = r
        d = {
            "$type": NS + "RectangleItem, SimHub.Plugins",
            "IsRectangleItem": True,
            "BackgroundColor": argb(self.fill) if not self.fill.startswith("#00") else self.fill,
            "BorderStyle": border,
        }
        d.update(self._common())
        return d

    def to_html(self):
        if not self.mock_visible():
            return ""
        s = self.sample
        x, w = s.get("x", self.x), s.get("w", self.w)
        y, h = s.get("y", self.y), s.get("h", self.h)
        fill = s.get("fill", self.fill)
        style = [
            "position: absolute", "left: %spx" % x, "top: %spx" % y,
            "width: %spx" % w, "height: %spx" % h, "box-sizing: border-box",
            "background: %s" % css_color(fill),
        ]
        if self.stroke and self.stroke_w:
            style.append("border: %spx solid %s" % (self.stroke_w, css_color(s.get("stroke", self.stroke))))
        if self.corners:
            tl, tr, bl, br = self.corners
            style.append("border-radius: %spx %spx %spx %spx" % (tl, tr, br, bl))
        return '<div style="%s"></div>' % "; ".join(style)


class Text(El):
    def __init__(self, x, y, w, h, text="", size=24, color="#FFFFFF", weight="Normal",
                 align="l", valign="c", font=FONT, bg=None, **kw):
        # WPF lays text out at ~1.2x the font size; give the box that much room
        # (grown around its centre, the box is transparent) so glyphs never clip.
        need = round(size * 1.25)
        if bg is None and h < need:
            y, h = y - (need - h) / 2.0, need
        super().__init__(x, y, w, h, **kw)
        self.text, self.size, self.color, self.weight = text, size, color, weight
        self.align, self.valign, self.font, self.bg = align, valign, font, bg

    def to_json(self):
        d = {
            "$type": NS + "TextItem, SimHub.Plugins",
            "IsTextItem": True,
            "Font": self.font,
            "FontWeight": self.weight,
            "FontSize": float(self.size),
            "Text": self.text,
            "TextColor": argb(self.color),
            "HorizontalAlignment": ALIGN_H[self.align],
            "VerticalAlignment": ALIGN_V[self.valign],
            "BackgroundColor": argb(self.bg) if self.bg else TRANSPARENT,
        }
        d.update(self._common())
        return d

    def to_html(self):
        if not self.mock_visible():
            return ""
        s = self.sample
        text = s.get("text", self.text)
        color = s.get("color", self.color)
        justify = {"l": "flex-start", "c": "center", "r": "flex-end"}[self.align]
        items = {"t": "flex-start", "c": "center", "b": "flex-end"}[self.valign]
        style = [
            "position: absolute", "left: %spx" % self.x, "top: %spx" % self.y,
            "width: %spx" % self.w, "height: %spx" % self.h,
            "display: flex", "align-items: %s" % items, "justify-content: %s" % justify,
            "font-size: %spx" % self.size, "font-weight: %s" % CSS_WEIGHT[self.weight],
            "color: %s" % css_color(color), "white-space: nowrap", "overflow: hidden", "line-height: 1",
        ]
        if self.bg or s.get("bg"):
            style.append("background: %s" % css_color(s.get("bg", self.bg)))
        return '<div style="%s">%s</div>' % ("; ".join(style), html.escape(str(text)))


class Group(El):
    """A Dash Studio layer. With `repeat`, SimHub draws the children `count`
    times, `dy` pixels apart, and `repeatindex()` (1-based) is available to
    formulas. `rows` supplies per-row mockup children (already built)."""

    def __init__(self, children, name="Layer", repeat=None, rows=None, **kw):
        xs = [c.x for c in children] or [0]
        ys = [c.y for c in children] or [0]
        x2 = [c.x + c.w for c in children] or [0]
        y2 = [c.y + c.h for c in children] or [0]
        super().__init__(min(xs), min(ys), max(x2) - min(xs), max(y2) - min(ys), name=name, **kw)
        self.children = children
        self.repeat = repeat
        self.rows = rows

    def to_json(self):
        d = {
            "$type": NS + "Layer, SimHub.Plugins",
            "Group": False,
            "Repetitions": self.repeat[0] if self.repeat else 0,
        }
        if self.repeat:
            d["PrepareRepetitions"] = True
            d["RepeatTopOffset"] = float(self.repeat[1])
        d["BackgroundColor"] = TRANSPARENT
        d["Childrens"] = [c.to_json() for c in self.children]
        d.update(self._common())
        return d

    def to_html(self):
        if not self.mock_visible():
            return ""
        if self.rows is not None:
            return "\n".join(c.to_html() for row in self.rows for c in row)
        return "\n".join(c.to_html() for c in self.children)


def repeated(count, dy, build, samples, name):
    """Build a repeating row layer. `build(sample)` returns the elements of
    one row positioned at the first row; formulas use repeatindex()."""
    template = build(samples[0])
    mock_rows = []
    for i, s in enumerate(samples[:count]):
        mock_rows.append([el.shifted(i * dy) for el in build(s)])
    return Group(template, name=name, repeat=(count, dy), rows=mock_rows)


def css_color(c):
    if c.startswith("#") and len(c) == 9:  # #AARRGGBB
        a = int(c[1:3], 16) / 255.0
        return "rgba(%d, %d, %d, %.3f)" % (int(c[3:5], 16), int(c[5:7], 16), int(c[7:9], 16), a)
    return c


# --------------------------------------------------------------------------
# Screens and dashboard
# --------------------------------------------------------------------------

class Screen:
    def __init__(self, name, items, role="ingame", trigger=None, bg="#06080A", enabled=None):
        if role == "overlay":
            # SimHub draws overlays on top of the current page and does not paint
            # their screen background, so lay a solid full-screen backdrop first.
            items = [Rect(0, 0, W, H, fill=bg, name="Backdrop")] + list(items)
        self.name, self.items, self.role, self.trigger, self.bg = name, items, role, trigger, bg
        self.enabled = enabled   # JS: page is in the next/previous rotation only while true

    def to_json(self):
        trig = {"Expression": ""}
        if self.trigger is not None:
            trig = {"Expression": jslib.program(self.trigger.body), "Interpreter": 1}
        return {
            "RenderingSkip": 0,
            "Name": self.name,
            "InGameScreen": self.role == "ingame",
            "IdleScreen": self.role == "idle",
            "PitScreen": False,
            "ScreenId": uid("screen/" + self.name),
            "AllowOverlays": True,
            "IsForegroundLayer": False,
            "IsOverlayLayer": self.role == "overlay",
            "OverlayTriggerExpression": trig,
            "ScreenEnabledExpression": ({"Expression": jslib.program(self.enabled.body), "Interpreter": 1}
                                        if self.enabled is not None else {"Expression": ""}),
            "OverlayMaxDuration": 0,
            "OverlayMinDuration": 0,
            "IsBackgroundLayer": False,
            "BackgroundColor": argb(self.bg),
            "MinimumRefreshIntervalMS": 0.0,
            "Items": [it.to_json() for it in self.items],
        }

    def to_html(self):
        return "\n".join(it.to_html() for it in self.items)
