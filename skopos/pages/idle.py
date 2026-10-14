"""IDLE: shown by SimHub when iRacing is not running (1920x720)."""

from ..dsl import Rect, Screen, Text
from ..theme import ACCENT, BG, BRAND, LABEL
from .common import value


def build(brand=BRAND):
    items = [
        Text(0, 150, 1920, 180, brand, size=160, weight="Bold", color=ACCENT, align="c", name="Wordmark"),
        Rect(860, 350, 200, 4, fill=ACCENT, radius=2, name="Rule"),
        value(0, 380, 1920, 110, "var d = new Date(); return pad2(d.getHours()) + ':' + pad2(d.getMinutes());",
              "21:42", size=96, align="c", refresh=1000, name="Clock"),
        Text(0, 500, 1920, 44, "Waiting for iRacing", size=28, weight="SemiBold", color=LABEL, align="c", name="Status"),
        Text(0, 650, 1920, 32, "Next / previous screen: map buttons in SimHub › Dash Studio › Controls",
             size=20, weight="SemiBold", color=LABEL, align="c", name="Hint"),
    ]
    return Screen("IDLE", items, role="idle", bg=BG)
