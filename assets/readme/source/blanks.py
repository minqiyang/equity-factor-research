"""Blanks (R6): a price gap in one held stock blanks every month it touches, in every book; nothing is filled.

Left: an illustration (not data). Three tapes of month cells; the cells that touch the gap are hatched in all three.
Right: run-of-record counts of blanked months (path_break_held), one cell per year, the hatched share of each cell
equal to that year's blanked months. Sources: reports/m55_screen_v1.md (screen 1963-07 to 1992-12, 215 of 354,
by year 1967 5, 1968-1984 12, 1985 6) and reports/m55_confirm_v1.md (confirm 1993-02 to 2014-03, 100 of 254, by
year 2003 10, 2004 12, 2005 12, 2006 10, 2007 11, 2008 12, 2009 12, 2010 12, 2011 9; check 0 of 114 months).
A partly blanked year puts its blanked months next to the neighbour year with more blanked months; the reports give
no month order inside a year. For confirm this gives the two spans of 44 and 56 months that the report states.
"""
import bm
from art import (DASH_LEADER, MARGIN, SIZE_LABEL, SIZE_NOTE, SIZE_VALUE, SW_HAIR, SW_MARK, Doc, walk)

W, H = 1200, 304
RH = 14                      # one cell height for both panels

# left: illustration ----------------------------------------------------------------------------
X0, N, PITCH, CG = 108, 16, 27.5, 3     # month cells: 16 x 27.5 = 440, so the tapes end at 548
X1 = X0 + N * PITCH
G0, G1 = 5.5, 8.5            # the price gap, in months: each edge sits mid-cell, the hatch takes whole cells
PY0, PY1 = 72, 136           # price band
RY, RG = 166, 6              # first tape top, tape gap
BOOKS = ("index", "tilt", "SPY")
DROP = 0.06                  # the level falls across the gap (illustration)
SEED = 59                    # a walk that rises into the gap and resumes lower

# right: run of record --------------------------------------------------------------------------
DIV = 580
XR = 612                     # both tapes start here, at one month pitch
MP = (W - MARGIN - XR) / 354            # month pitch, 1.525: the 354 screen months fill the panel


def _years(first, last, months_first, months_last, blanked):
    out = {}
    for y in range(first, last + 1):
        m = 12
        if y == first:
            m = months_first
        elif y == last:
            m = months_last
        out[y] = (m, blanked.get(y, 0))
    return out


SCREEN = _years(1963, 1992, 6, 12, {1967: 5, **{y: 12 for y in range(1968, 1985)}, 1985: 6})
CONFIRM = _years(1993, 2014, 11, 3, {2003: 10, 2004: 12, 2005: 12, 2006: 10, 2007: 11, 2008: 12, 2009: 12,
                                     2010: 12, 2011: 9})
assert sum(m for m, _ in SCREEN.values()) == 354 and sum(b for _, b in SCREEN.values()) == 215
assert sum(m for m, _ in CONFIRM.values()) == 254 and sum(b for _, b in CONFIRM.values()) == 100
PERIODS = (("screen", SCREEN, 215, 354), ("confirm", CONFIRM, 100, 254))


def tx(t: float) -> float:
    return X0 + t * PITCH


def hatch(d: Doc, x: float, y: float, w: float, h: float, cls: str = "mute", step: float = 6.0):
    """45-degree hairlines clipped to the rectangle, phase fixed to the page so neighbours line up."""
    segs = []
    k = int((x + y) // step)
    while k * step <= x + w + y + h:
        c = k * step
        lo, hi = max(x, c - (y + h)), min(x + w, c - y)
        if hi - lo > 1.5:                       # drop corner slivers that read as dots
            segs.append(f"M{lo:.2f} {c - lo:.2f}L{hi:.2f} {c - hi:.2f}")
        k += 1
    if segs:
        d.path("".join(segs), cls, SW_HAIR)


def price_path():
    """art.walk at about 6 points a month; the points inside the gap are not drawn."""
    n = 97
    lv = walk(n, seed=SEED)
    ts = [i * N / (n - 1) for i in range(n)]

    def at(t):                                   # linear level at time t
        i = min(int(t / (N / (n - 1))), n - 2)
        f = (t - ts[i]) / (ts[i + 1] - ts[i])
        return lv[i] + f * (lv[i + 1] - lv[i])

    before = [(t, v) for t, v in zip(ts, lv) if t < G0] + [(G0, at(G0))]
    after = [(G1, at(G1) - DROP)] + [(t, v - DROP) for t, v in zip(ts, lv) if t > G1]
    lo = min(v for _, v in before + after)
    hi = max(v for _, v in before + after)
    sc = lambda v: PY1 - (v - lo) / (hi - lo) * (PY1 - PY0)  # noqa: E731
    return [(tx(t), sc(v)) for t, v in before], [(tx(t), sc(v)) for t, v in after]


def poly(pts) -> str:
    return "M" + "L".join(f"{x:.2f} {y:.2f}" for x, y in pts)


def xmark(d: Doc, x: float, y: float, r: float = 4.0):
    d.path(f"M{x - r:.2f} {y - r:.2f}L{x + r:.2f} {y + r:.2f}M{x - r:.2f} {y + r:.2f}L{x + r:.2f} {y - r:.2f}",
           "ink", SW_MARK)


def months_of(years: dict) -> list[bool]:
    """One flag per month of the period, True when blanked."""
    ys, out = sorted(years), []
    for k, yr in enumerate(ys):
        months, nb = years[yr]
        prev_b = years[ys[k - 1]][1] if k > 0 else 0
        next_b = years[ys[k + 1]][1] if k + 1 < len(ys) else 0
        flags = [True] * nb + [False] * (months - nb)
        out += flags if prev_b >= next_b else flags[::-1]
    return out


def tape(d: Doc, x: float, y: float, flags: list[bool]):
    """Runs of counted months are solid, runs of blanked months are hatched; no gaps between months."""
    i = 0
    while i < len(flags):
        j = i
        while j < len(flags) and flags[j] == flags[i]:
            j += 1
        x0, w = x + i * MP, (j - i) * MP
        if flags[i]:
            hatch(d, x0, y, w, RH)
        else:
            d.rect(x0, y, w, RH, "ink")
        i = j


def tag_left_panel(d: Doc):
    """art.illustration_tag places the tag at the image's top right, which here is the data panel; this puts the
    same tag (13 mute, baseline 50, right-aligned) at the top right of the illustration panel."""
    d.text("illustration", X1, 50, SIZE_NOTE, "mute", anchor="end")


def build():
    d = Doc("blanks", W, H)

    # --- illustration ---
    tag_left_panel(d)
    before, after = price_path()
    for pts in (before, after):
        d.path(poly(pts), "ink", SW_MARK, extra='stroke-linejoin="round" stroke-linecap="round"')
    for x, y in (before[-1], after[0]):
        xmark(d, x, y)
        d.line(x, y + 9, x, RY - 6, "mute", SW_HAIR, DASH_LEADER)

    blank = [i for i in range(N) if i + 1 > G0 and i < G1]
    for r, name in enumerate(BOOKS):
        y = RY + r * (RH + RG)
        d.text(name, MARGIN, y + RH - 2, SIZE_LABEL, "ink")
        for i in range(N):
            x, w = tx(i) + CG / 2, PITCH - CG
            if i in blank:
                hatch(d, x, y, w, RH)
            else:
                d.rect(x, y, w, RH, "ink")
    rows_bot = RY + len(BOOKS) * RH + (len(BOOKS) - 1) * RG

    # the one accent: the span that is blanked, half a cell wider than the gap at each end
    bx0, bx1 = tx(blank[0]) + CG / 2, tx(blank[-1] + 1) - CG / 2
    yb = rows_bot + 16
    d.path(f"M{bx0:.2f} {yb - 6:.2f}L{bx0:.2f} {yb:.2f}L{bx1:.2f} {yb:.2f}L{bx1:.2f} {yb - 6:.2f}", "accent", SW_MARK)
    base = yb + 24
    d.text("blanked in every book, never filled", (bx0 + bx1) / 2, base, SIZE_LABEL, "accent", anchor="middle")

    # --- run of record ---
    d.line(DIV, 40, DIV, base, "hair", SW_HAIR)
    d.text("run of record", XR, 50, SIZE_NOTE, "mute")
    num_x = XR + max(bm.width(p[0], SIZE_LABEL) for p in PERIODS) + 16 + bm.width("000", SIZE_VALUE, "bold")

    def count_line(name, b, total, base_y):
        d.text(name, XR, base_y, SIZE_LABEL, "ink")
        d.text(str(b), num_x, base_y, SIZE_VALUE, "ink", "bold", anchor="end")
        d.text(f"of {total} months blank", num_x + 8, base_y, SIZE_NOTE, "mute")

    tops = (106, RY + RH + RG)                     # confirm tape level with the tilt tape
    for (name, years, b, total), top in zip(PERIODS, tops):
        count_line(name, b, total, top - 10)
        flags = months_of(years)
        assert len(flags) == total and sum(flags) == b
        tape(d, XR, top, flags)
        ys = sorted(years)
        yt = top + RH + 18
        d.text(str(ys[0]), XR, yt, SIZE_NOTE, "mute")
        d.text(str(ys[-1]), XR + total * MP, yt, SIZE_NOTE, "mute", anchor="end")
    count_line("check", 0, 114, base)
    return d


if __name__ == "__main__":
    build().write()
