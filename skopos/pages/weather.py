"""WEATHER: conditions at a glance (1920x720)."""

from ..dsl import Screen, Text
from ..theme import (GARAGE_PAGES, INFO, LABEL, TEXT, WARN, argb)
from .common import chrome_bottom, panel, value

TREND = (" if (d === null) { return 'collecting trend…'; }"
         " if (Math.abs(d) < 0.25) { return 'steady over last 10 min'; }"
         " return (d > 0 ? '▲ ' : '▼ ') + Math.abs(d).toFixed(1) + '° over last 10 min';")
TREND_COL = (" if (d === null || Math.abs(d) < 0.25) { return '%s'; } return d > 0 ? '%s' : '%s';"
             % (argb(LABEL), argb(WARN), argb(INFO)))


HW = (1904 - 10) // 2                   # two heroes side by side, full width
TW, TH = 468, 186                       # tiles: 4 x 2
TX = [8 + k * (TW + 10) for k in range(4)]
TY = [286, 482]


def hero(x, title, getter, key, sample, trend_sample, trend_col):
    get = "var v = %s;" % getter
    tr = get + " var d = trend('%s', v, 600);" % key
    return [
        panel(x, 14, HW, 262, title + " panel", title=title),
        value(x + 24, 34, 640, 170, get + " return fx(v, 1);", sample, size=150, align="r", refresh=2000, name=title),
        Text(x + 676, 96, 160, 70, "\u00b0C", size=56, weight="SemiBold", color=LABEL, name=title + " unit"),
        value(x + 24, 222, HW - 48, 38, tr + TREND, trend_sample, size=26, weight="SemiBold", refresh=5000,
              color_js=tr + TREND_COL, sample_color=trend_col, name=title + " trend"),
    ]


def tile(x, y, title, js, sample, sub_js, sub_sample, size=50):
    return [
        panel(x, y, TW, TH, title + " tile", title=title),
        value(x + 24, y + 34, TW - 48, 90, js, sample, size=size + 10, refresh=2000, name=title),
        value(x + 24, y + 136, TW - 48, 32, sub_js, sub_sample, size=22, weight="SemiBold", color=LABEL,
              refresh=2000, name=title + " sub"),
    ]


def build(garage=False):
    items = []
    items += hero(8, "TRACK TEMP", "trackT()", "tt", "38.2", "\u25b2 1.4\u00b0 over last 10 min", WARN)
    items += hero(8 + HW + 10, "AIR TEMP", "airT()", "at", "24.1", "steady over last 10 min", LABEL)

    xs, ys = TX, TY
    tiles = [
        ("TRACK STATE", "return wetStr(TN('TrackWetness', 0));", "Dry",
         "return B('DataCorePlugin.GameRawData.Telemetry.WeatherDeclaredWet') ? 'declared WET' : 'declared dry';", "declared dry", 42),
        ("RAIN", "var p = TN('Precipitation', null); return p === null ? '—' : Math.round(p * 100) + '%';", "0%",
         "return skiesStr(TN('Skies', -1));", "Partly cloudy", 50),
        ("WIND", "var v = TN('WindVel', null); return v === null ? '—' : fx(v * 3.6, 0) + ' km/h';", "12 km/h",
         "var d = TN('WindDir', null); return d === null ? '' : 'direction ' + compass(d);", "direction NW", 50),
        ("HUMIDITY", "var h = TN('RelativeHumidity', null); return h === null ? '—' : Math.round(h * 100) + '%';", "55%",
         "var f = TN('FogLevel', null); return f === null ? '' : 'fog ' + Math.round(f * 100) + '%';", "fog 0%", 50),
        ("AIR PRESSURE", "var p = hPa(TN('AirPressure', null)); return p === null ? '—' : fx(p, 0) + ' hPa';", "1013 hPa",
         "var d = TN('AirDensity', null); return d === null ? '' : 'density ' + fx(d, 3) + ' kg/m³';", "density 1.191 kg/m³", 46),
        ("TIME AT TRACK", "var t = TN('SessionTimeOfDay', null); if (t === null) { return '—'; } t = t % 86400;"
         " return pad2(Math.floor(t / 3600)) + ':' + pad2(Math.floor((t % 3600) / 60));", "14:32",
         "var a = TN('SolarAltitude', null); if (a === null) { return ''; } a = a * 180 / Math.PI;"
         " return a < 0 ? 'night (sun below horizon)' : 'sun ' + Math.round(a) + '° above horizon';",
         "sun 34° above horizon", 50),
        ("TRACK RUBBER", "return rubber();", "Moderate",
         "return 'track usage';", "track usage", 36),
        ("TRACK", "return shortName(nz(S('WeekendInfo.TrackDisplayShortName', null), P('TrackName', '—')), 16);", "Spa",
         "var l = trackLenM(), p = pitLimitKph(); return (l > 0 ? (l / 1000).toFixed(2) + ' km' : '') + (p > 0 ? '  ·  pit ' + Math.round(p) + ' km/h' : '');",
         "7.00 km  ·  pit 60 km/h", 42),
    ]
    for k, (title, js, sample, sub, sub_s, size) in enumerate(tiles):
        items += tile(xs[k % 4], ys[k // 4], title, js, sample, sub, sub_s, size)
    items += chrome_bottom("WEATHER", GARAGE_PAGES if garage else None)
    return Screen("WEATHER (garage)" if garage else "WEATHER", items)
