"""Journey: how the program got here, 2026-05-21 to 2026-10-11.

The time axis is linear in days in two pieces. The 116 days from 2026-05-21 to 09-13 are drawn short, with month
ticks only, behind an axis break; a note says "116 days". The 28 days from 09-14 to 10-11 are drawn large with one
tick per day ("1 tick = 1 day"). A wall on 10-11 (O-23, PR #309) closes the axis and the data band.
Sources: facts.md (data over time 1-5, O-22 on 2026-10-05) and git on main: #245 and #246 (EODHD loader and
the first real-data runner) merged 2026-09-20, so the EODHD band starts that day; EODHD books stayed in use
after 09-28, so the next band is "+ public factor libraries" (added to EODHD, not in place of it). SEC EDGAR came
with O-10 on 2026-09-30, so "+ SEC" hangs from its own tick on that day inside the same band segment.
"""
from datetime import date

import bm
from art import MARGIN, SIZE_LABEL, SIZE_NOTE, SW_HAIR, SW_MARK, SW_WALL, Doc

W, H = 1200, 336
D0, DB, D1 = date(2026, 5, 21), date(2026, 9, 14), date(2026, 10, 11)
XL0, XL1 = MARGIN + 4, 204      # short piece: 2026-05-21 .. 2026-09-13 (the start dot's edge is at x = 48)
XR0, XR1 = 228, W - MARGIN - 2  # large piece: 2026-09-14 .. 2026-10-11 (the wall's right edge is at x = 1152)
KL = (XL1 - XL0) / (DB - D0).days
KR = (XR1 - XR0) / (D1 - DB).days

TOP = {1: 40, 2: 120}           # top of each flag (stem top, cap line of the date)
AX = 200                        # axis
BAND, BH = 248, 6               # data band top and height
DOT = 3.5

# date, label, outcome, level, side the text hangs on
STOPS = [
    (D0, "start", "engine", 1, "r"),
    (date(2026, 9, 16), "demo v0", "synthetic", 2, "r"),
    (date(2026, 9, 19), "52 alphas", "exploratory", 2, "r"),
    (date(2026, 9, 26), "S&P 500 point in time", "too little power", 1, "l"),
    (date(2026, 9, 28), "North Star v2", "factor classes", 1, "r"),
    (date(2026, 9, 30), "class allocator", "none beat SPY", 2, "r"),
    (date(2026, 10, 10), "index tilt", "stopped at floor", 2, "l"),
    (D1, "O-23", "no reliable edge", 1, "l"),
]

# data in use: start day (inclusive), label lines, fill style
SEC = date(2026, 9, 30)         # O-10: SEC EDGAR added inside the 09-28 segment, labelled on the second line
DATA = [
    (D0, ["synthetic"], "hollow"),
    (date(2026, 9, 20), ["EODHD snapshots"], "faint"),
    (date(2026, 9, 28), ["+ public factor libraries"], "mute"),
    (date(2026, 10, 5), ["WRDS CRSP 1963-2025"], "ink"),
]

boxes: list[tuple[float, float, float, float, str]] = []


def tx(d: date) -> float:
    if d < DB:
        return XL0 + (d - D0).days * KL
    return XR0 + (d - DB).days * KR


def put(doc: Doc, t: str, x: float, y: float, size: float, cls: str, anchor: str = "start"):
    """Draw text and keep its box (cap line to descender), so a collision check can run at the end."""
    w = bm.width(t, size)
    x0 = x - (w if anchor == "end" else w / 2 if anchor == "middle" else 0)
    boxes.append((x0, y - size * 0.68, x0 + w, y + size * 0.245, t))
    doc.text(t, x, y, size, cls, "regular", anchor)


def check() -> None:
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            if a[0] < b[2] + 6 and b[0] < a[2] + 6 and a[1] < b[3] + 4 and b[1] < a[3] + 4:
                print(f"collision: {a[4]!r} / {b[4]!r}")
        if a[0] < MARGIN or a[2] > W - MARGIN or a[1] < 40 or a[3] > H - 40:
            print(f"frame: {a[4]!r} {a[:4]}")


def build():
    boxes.clear()
    d = Doc("journey", W, H)

    # axis: the short piece has month ticks only, the large piece one tick per day
    d.line(XL0, AX, XL1, AX, "mute", SW_HAIR)
    d.line(XR0, AX, XR1, AX, "mute", SW_HAIR)
    day = D0
    while day <= D1:
        x = tx(day)
        if day.day == 1:
            d.line(x, AX, x, AX + 10, "mute", SW_HAIR)
            put(d, day.strftime("%b").lower(), x, AX + 28, SIZE_NOTE, "mute", "middle")
        elif day >= DB:
            d.line(x, AX, x, AX + 6, "faint", SW_HAIR)
        day = date.fromordinal(day.toordinal() + 1)
    put(d, "116 days", (XL0 + XL1) / 2, AX - 12, SIZE_NOTE, "mute", "middle")
    put(d, "1 tick = 1 day", XR0 + 8, AX + 28, SIZE_NOTE, "mute")

    # axis break, drawn on the axis and on the band
    xm = (XL1 + XR0) / 2
    for yc in (AX, BAND + BH / 2):
        for xb in (xm - 3, xm + 3):
            d.line(xb - 3, yc + 7, xb + 3, yc - 7, "mute", SW_HAIR)

    # data band, in the same two pieces; it ends at the wall
    wall_l = XR1 - SW_WALL / 2
    ends = [s for s, _, _ in DATA[1:]] + [None]
    for (start, lines, style), end in zip(DATA, ends):
        xa = tx(start) + (1.5 if start != D0 else 0)
        xb = (tx(end) - 1.5) if end else wall_l
        pieces = [(xa, XL1), (XR0, xb)] if start < DB < (end or D1) else [(xa, xb)]
        for pa, pb in pieces:
            if style == "hollow":
                d.path(f"M{pa + 0.5:.2f} {BAND + 0.5}H{pb - 0.5:.2f}V{BAND + BH - 0.5}H{pa + 0.5:.2f}Z", "faint",
                       SW_HAIR)
            elif style == "ink":
                d.rect(pa, BAND + 1, pb - pa, BH - 2, "ink")      # same weight as the 6 px fills, not heavier
            else:
                d.rect(pa, BAND, pb - pa, BH, style)
        x = tx(start)
        d.line(x + 0.5, BAND + BH + 4, x + 0.5, BAND + BH + 20, "faint", SW_HAIR)
        for k, t in enumerate(lines):
            put(d, t, x + 8, BAND + BH + 18 + 20 * k, SIZE_NOTE, "mute")
    x = tx(SEC)
    d.line(x + 0.5, BAND + BH + 26, x + 0.5, BAND + BH + 40, "faint", SW_HAIR)
    put(d, "+ SEC", x + 8, BAND + BH + 38, SIZE_NOTE, "mute")

    # stops
    for day, lab, out, lvl, side in STOPS:
        x = tx(day)
        top = TOP[lvl]
        last = day == D1
        if last:
            d.line(x, top, x, AX - 12, "accent", SW_MARK)
            d.rect(wall_l, AX - 12, SW_WALL, BAND + BH + 8 - (AX - 12), "accent")
        else:
            d.line(x, top, x, AX, "faint", SW_HAIR)
            d.circle(x, AX, DOT, "ink")
        gap = 10 if last else 8
        tx_ = x + gap if side == "r" else x - gap
        anc = "start" if side == "r" else "end"
        put(d, "2026-05-21" if day == D0 else day.strftime("%m-%d"), tx_, top + 9, SIZE_NOTE, "mute", anc)
        put(d, lab, tx_, top + 31, SIZE_LABEL, "ink", anc)
        put(d, out, tx_, top + 53, SIZE_LABEL if last else SIZE_NOTE, "accent" if last else "mute", anc)
    check()
    return d


if __name__ == "__main__":
    build().write()
