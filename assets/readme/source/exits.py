"""Exits (R4): how a held stock that leaves is settled, and the rerun that checks the choice.

Counts: confirm segment, CW-PIT book, reports/m55_confirm_v1.md table "r4, CW-PIT held disappearances by cause".
Primary loader run, 303 held: 301 ciz_return_in_path + 1 supplied_terminal_return use a real exit return (302);
1 missing_engine_default (cause unknown) settles at -100% (line 51); no cash merger takes the default.
last_close run: 320 held, a separate loader run with its own held set. Composite: no sign flip (line 35).
"""
import bm
from art import (DASH_OPEN, MARGIN, SIZE_LABEL, SIZE_NOTE, SIZE_VALUE, SW_HAIR, SW_MARK, Doc, arrow_head,
                 walk)

W, H = 1200, 376
CAP, YES, TRUNK, NO, FAIL, RUN2 = 52, 104, 160, 216, 264, 328
DOT = 152                     # the last close: where both tracks start
COL1 = DOT + 16               # trunk and rerun labels
D1 = 368                      # "exit return in the data?"
R = 5 * 2 ** 0.5              # a decision: a 10 px stage node turned 45 degrees
COL2 = D1 + 24                # yes and no labels
FORK = 576                    # the cause default splits
COL3 = FORK + 24              # the two default rules
BR = 848                      # the primary run gathers
GAP = 8                       # space each side of a count set into its line


def label(d: Doc, x: float, y: float, cond: str, act: str, act_cls: str = "ink") -> None:
    """'cond: act' above a line at y, the condition in mute and the action in ink (or accent)."""
    lead = f"{cond}: "
    d.text(lead, x, y - 14, SIZE_LABEL, "mute")
    d.text(act, x + bm.width(lead, SIZE_LABEL), y - 14, SIZE_LABEL, act_cls)


def run(d: Doc, x0: float, x1: float, y: float, n: str, nx: float, cls: str = "mute", sw: float = SW_HAIR,
        n_cls: str = "ink") -> None:
    """A line from x0 to x1 at y, broken around the count n (16 bold) set into it at nx."""
    w = bm.width(n, SIZE_VALUE, "bold")
    if nx - GAP - x0 > GAP:
        d.line(x0, y, nx - GAP, y, cls, sw)
    d.text(n, nx, y + 5.5, SIZE_VALUE, n_cls, "bold")
    d.line(nx + w + GAP, y, x1, y, cls, sw)


def diamond(d: Doc, x: float, y: float) -> None:
    d.path(f"M{x - R} {y}L{x} {y - R}L{x + R} {y}L{x} {y + R}Z", "ink", SW_MARK)


def build():
    d = Doc("exits", W, H)
    d.text("confirm 1993-2014, our index, counts of held exits", MARGIN, CAP, SIZE_NOTE, "mute")

    # the held stock: an illustrative price path that stops at its last close
    v = walk(27, seed=98)
    k = 30 / (max(v) - min(v))
    pts = [(MARGIN + 4 * i, TRUNK - (x - v[-1]) * k) for i, x in enumerate(v)]
    d.path("M" + "L".join(f"{x:.2f} {y:.2f}" for x, y in pts), "ink", SW_MARK)
    d.circle(DOT, TRUNK, 3.5, "ink")

    # primary run: every held exit asks one question first
    d.text("held stock leaves", COL1, TRUNK - 14, SIZE_LABEL, "ink")
    d.text("primary run", COL1, TRUNK + 28, SIZE_NOTE, "mute")
    run(d, DOT + 3.5 + GAP, D1 - R - 1, TRUNK, "303", COL1)
    arrow_head(d, D1 - R - 1, TRUNK)
    diamond(d, D1, TRUNK)
    d.text("exit return known?", COL2, TRUNK + 5, SIZE_LABEL, "ink")

    # yes: the return already in the data settles the exit
    d.path(f"M{D1} {TRUNK - R}V{YES}H{COL2 - GAP}", "mute", SW_HAIR)
    label(d, COL2, YES, "yes", "use it")
    run(d, COL2, BR + 0.5, YES, "302", COL2)

    # no: the cause default, which splits by cause
    d.path(f"M{D1} {TRUNK + R}V{NO}H{COL2 - GAP}", "mute", SW_HAIR)
    label(d, COL2, NO, "no", "cause default")
    run(d, COL2, FORK, NO, "1", COL2)
    d.line(FORK, NO, COL3 - GAP, NO, "mute", SW_HAIR)
    label(d, COL3, NO, "cash merger", "last close")
    run(d, COL3, BR, NO, "0", COL3)
    d.path(f"M{FORK} {NO}V{FAIL}H{COL3 - GAP}", "accent", SW_MARK)
    label(d, COL3, FAIL, "failure or unknown", "−100%", "accent")
    run(d, COL3, BR + 0.5, FAIL, "1", COL3, "accent", SW_MARK, "accent")

    # the comparison: the right block ends on the frame edge
    fw = bm.width("fragile", SIZE_LABEL) + 16
    box_x = W - MARGIN - fw
    arr_x1 = box_x - 8
    sf_w = bm.width("sign flip?", SIZE_LABEL)
    cmp_x = (arr_x1 - 32 - 12 - sf_w - 24) // 8 * 8      # the comparison diamond on the 8 px grid
    sf_x = cmp_x + 24
    arr_x0 = sf_x + sf_w + 12

    d.line(BR, YES - 0.5, BR, FAIL + 0.75, "mute", SW_HAIR)
    d.line(BR, TRUNK, cmp_x - R - 1, TRUNK, "mute", SW_HAIR)
    arrow_head(d, cmp_x - R - 1, TRUNK)

    # second run: a separate loader run with its own held set
    d.circle(DOT, RUN2, 3.5, "ink")
    label(d, COL1, RUN2, "second run", "every exit at its last close")
    run(d, DOT + 3.5 + GAP, cmp_x + 0.5, RUN2, "320", COL1)
    d.line(cmp_x, RUN2 + 0.5, cmp_x, TRUNK + R + 1, "mute", SW_HAIR)
    arrow_head(d, cmp_x, TRUNK + R + 1, "up")
    diamond(d, cmp_x, TRUNK)

    d.text("sign flip?", sf_x, TRUNK + 5, SIZE_LABEL, "ink")
    d.line(arr_x0, TRUNK, arr_x1 - 7, TRUNK, "mute", SW_HAIR, DASH_OPEN)
    arrow_head(d, arr_x1, TRUNK)
    d.path(f"M{box_x + 0.5} {TRUNK - 14.5}h{fw - 1}v29h{-(fw - 1)}z", "mute", SW_HAIR)
    d.text("fragile", box_x + 8, TRUNK + 5, SIZE_LABEL, "mute")
    d.text("composite: no sign flip", sf_x, TRUNK + 40, SIZE_NOTE, "mute")
    return d


if __name__ == "__main__":
    build().write()
