# SKOPOS: iRacing dashboard for SimHub

A SimHub Dash Studio dashboard for iRacing, made for a **12.3" 1920×720 bar display** used as a 4th monitor. The layout, font sizes and page set are designed for that 8:3 screen; on other screen shapes SimHub scales it with black bars.

The dashboard is generated from Python (`build.py`), so the layout lives in code and no dashboard update can overwrite your changes. *Skopos* (σκοπός) is Ancient Greek for the mark you aim at.

## Install (Windows)

1. Copy `dist/SKOPOS.simhubdash` to the PC and double-click it. Or open SimHub › **Dash Studio** › **Import dashboard** and pick the file.
   If you prefer doing it by hand, copy the `dist/SKOPOS` folder to `C:\Program Files (x86)\SimHub\DashTemplates\SKOPOS`.
2. In Dash Studio, open **SKOPOS** in a window, move the window to the 4th screen and make it fullscreen.
3. Map **Next screen** / **Previous screen** to wheel buttons in SimHub (Controls and events › Dash Studio). You can also hover the dash window to get SimHub's on-screen arrows.

Optional: **Romainrob's iRacing Extra Properties** (SimHub forum › Dashboard Templates › "Romainrob's collection"). Copy the plugin DLL into the SimHub folder, restart, and enable it under *Add/Remove features*. It adds:
iRating gain estimate, gap trend to the car ahead, distance to pit **entry**, and licence strings on the relative. Everything else works on stock SimHub.
MorGuux's SwitchableProperties is **not** needed. Pages use SimHub's built-in next/previous screen.

## Pages

| Page | What it shows |
|---|---|
| RACE | The only page with the 20-LED shift lights; at the shift point the LEDs and gear box flash **red / yellow**. On top: Δ to **your session best** with bar and your best lap. Big gear. Porsche-style timing: big LAPTIME box, LAST LAP and PRED. TIME boxes. CAR AHEAD and CAR BEHIND boxes (**relative**: the cars directly ahead / behind on track): position and number, name, iR and SR in licence colour (iR red + full-width flashing LOW iRATING banner below 2000), gap, and the car they drive. Right column top to bottom: MAP / TC / BB / ABS (the BB box fills red when you change brake bias and fades back over 2 s); fuel per lap, fuel laps, last lap, to finish; session: fuel left, iR estimate, SoF, laps left, time left, incidents |
| TIMING | The **whole field** in one column in the middle of the screen, for joining a session and during / after qualifying: cars with a lap time first (fastest first), then everyone else by iRating. Holds 24 drivers; with more, the top 12 and bottom 12 are shown, an orange line marks the hidden middle and the footer says how many are hidden. Columns: position, car number (class colour), name, car, licence + SR, iR, best lap (fastest in purple), gap to the fastest. Car count, cars with a time and SoF in the footer |
| FUEL | Fuel in tank, litres to add at the next stop (with 0.5 lap margin), stops needed, per-lap average and last lap, laps/time on fuel, race laps/time left, fuel-save target to skip the stop, pit window |
| FIELD (garage only) | Only in the garage and only in **multi-class** sessions. One column per class (fastest class first, up to 3), with the class **SoF** and car count in the header, then drivers in class-position order: car number, name, iR, licence + SR. In single-class sessions the garage shows Timing only |
| WEATHER | Track and air temp with 10-minute trend, track wetness, rain, sky, wind, humidity, fog, pressure, air density, time of day / sun, rubber, track info |
| PIT (overlay) | Pops up over any page **only while the pit limiter is on**. Fuel now, add to finish, fuel set for the stop, tyres, repairs across the top; metres to pit entry / pit box big and centred at the bottom with 100 m / 30 m markers and a BRAKE cue |
| IDLE | Clock while iRacing is not running |

**In the garage** (not in the car on track) next / previous cycles **Timing → Weather → Field** (Field only in multi-class sessions); the driving pages are switched off there.

Notes

- Delta is iRacing's own **session best** delta (your best clean lap this session), the same number as the in-game delta bar; it shows "—" while iRacing flags it invalid. Predicted lap and "your best" use that same reference lap, which the dash learns at each lap line (a faster lap with an incident does not replace it, as in iRacing). Until the first reference exists, predicted uses your last lap + iRacing's delta to it.
- Laps left counts the lap you're on: 2 on the lap before the white flag, 1 on the white-flag lap. In timed races it includes the lap after the clock runs out.
- There is no tyre page: iRacing only sends tyre temps and wear while you're stopped in your box.
- Pit box distance comes from iRacing's own pit stall position (`DriverPitTrkPct`), so no plugin or "learning lap" is required.

## Editing

```
python3 build.py              # regenerate dist/ and the mockups
python3 tests/check_formulas.py   # run every formula against simulated data (macOS JavaScriptCore)
python3 tests/check_reference_lap.py   # lap-by-lap test of the delta reference / predicted lap
python3 tests/check_laps_left.py   # laps left at the end of timed and lap races
python3 tests/check_bb_fade.py   # brake-bias change highlight over time
```

- `skopos/pages/common.py`: panel look (`STYLE`: `bordered` = black boxes with outline titles, `flat` = the old grey cards) and the Porsche-style header boxes used for lap timing
- `skopos/theme.py`: colours, font (Bahnschrift, built into Windows), tyre temperature bands, fuel margin, page order
- `skopos/pages/*.py`: one file per page, absolute pixel layout
- `skopos/jslib.py`: shared JavaScript helpers; each formula only gets the helpers it uses
- `build/preview.html`: all pages rendered with sample data for a quick look in a browser
