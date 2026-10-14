"""Visual system shared by every page (and by the mockups)."""

# Bahnschrift ships with Windows 10/11 (DIN-style, tabular digits) so the
# dashboard needs no font install. Mockups fall back to Barlow on the web.
FONT = "Bahnschrift"

# dashboard name: idle-screen logo (the SimHub dashboard / file name is NAME in build.py)
BRAND = "SKOPOS"

W, H = 1920, 720   # 12.3" bar display

# usable area between the shift lights and the footer tabs
TOP, BOTTOM = 46, 664

# Colours as #RRGGBB; argb() converts to SimHub's #AARRGGBB.
BG = "#06080A"
PANEL = "#0E1217"
PANEL_HI = "#151A21"
LINE = "#1E252E"
LABEL = "#8B95A1"
TEXT = "#F2F4F7"
DIM = "#525B66"
OFF = "#161B21"
ACCENT = "#FF8A1F"
ACCENT_BG = "#2A1A0A"
GOOD = "#2BD46B"
BAD = "#FF4D4D"
WARN = "#FFC53D"
INFO = "#3DA5FF"
PURPLE = "#B06CFF"   # session best (fastest lap of anyone)
PIT_BLUE = "#1E6FE0"
LAP_UP = "#FF7A7A"    # car a lap (or more) ahead of you
LAP_DOWN = "#6CB8FF"  # car you are lapping

# Tyre carcass temperature gradient (deg C): cold -> optimal -> hot.
TYRE_COLD, TYRE_OK, TYRE_HOT = INFO, GOOD, BAD
TYRE_T_COLD, TYRE_T_OK, TYRE_T_HOT = 60.0, 85.0, 110.0

# Race page: warn about the car ahead / behind below this iRating.
LOW_IR = 2000

# Fuel strategy: extra fuel (in laps) added on top of "needed to finish".
FUEL_MARGIN_LAPS = 0.5

PAGES = ["RACE", "FUEL", "TIMING", "WEATHER"]
GARAGE_PAGES = ["TIMING", "WEATHER", "FIELD"]   # the only pages while you are in the garage (FIELD: multi-class only)


def argb(hex_rgb, alpha=255):
    h = hex_rgb.lstrip("#")
    if len(h) == 8:
        return "#" + h.upper()
    return "#%02X%s" % (alpha, h.upper())


TRANSPARENT = "#00FFFFFF"
