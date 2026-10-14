from ..dsl import JS
from . import field, fuel, idle, pit, race, timing, weather

# In-game pages cycle in this order with SimHub's next/previous screen buttons.
IN_GAME = [race, fuel, timing, weather]


def screens():
    """Garage pages come first: when you enter the garage the driving pages
    switch off and SimHub moves on to the next enabled page, which wraps
    around to Timing. In the garage next/previous cycles Timing, Weather and
    (multi-class only) Field. Leaving works the same way back to Race."""
    in_garage, driving = JS("return garageMode();"), JS("return !garageMode();")
    tim, wea, fld = timing.build(garage=True), weather.build(garage=True), field.build_garage()
    tim.enabled = wea.enabled = in_garage
    fld.enabled = JS("return garageMode() && classCount() >= 2;")
    garage = [tim, wea, fld]
    drive = [p.build() for p in IN_GAME]
    for s in drive:
        s.enabled = driving
    return [idle.build()] + garage + drive + [pit.build()]
