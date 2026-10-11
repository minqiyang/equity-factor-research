"""Guards: the twelve research-safety invariants R1-R12 as one plate of glyphs (illustration, not data).

Each glyph has exactly one accent mark, at the point where its rule bites.
"""
import math

import bm
from art import (DASH_OPEN, MARGIN, SIZE_LABEL, SIZE_NOTE, SW_HAIR, SW_MARK, SW_WALL, Doc, arrow_head, walk)

W = 1200
COLS = 6
X0, X1 = MARGIN, W - MARGIN
CW = (X1 - X0) / COLS          # 184 px a column; glyph and labels start on the column line
S = 80                         # glyph box
TOP = 40                       # first glyph top
WORD = SIZE_NOTE               # word label size: at 15 "every trial counted" runs into "honest claims"
NUM_GAP = 30                   # glyph bottom to the R-number baseline
LINE = 20                      # R-number baseline to the word baseline
RULE_GAP = 22                  # word baseline to the rule under the row
ROW = S + NUM_GAP + LINE + RULE_GAP + 32     # 184: 32 from a rule to the next glyph top
LAST_RULE = TOP + ROW + S + NUM_GAP + LINE + RULE_GAP
H = -(-(LAST_RULE + 4 + 40) // 8) * 8        # bottom rule ticks end 4 below it
R = 3.5                        # glyph dot radius
HATCH = [5 + 8 * i for i in range(9)]        # hatch feet 5..69, heads to 75: centred on 40


# glyphs, each drawn in an 80 x 80 box at the origin -------------------------------------------------------------
def g_timing(d):
    """R1: days known before the decision sit left of the wall; after it the axis is not read."""
    y = 48
    d.line(0, y, 48, y, "mute", SW_HAIR)
    for x in (8, 22, 36):
        d.circle(x, y, R, "ink")
    d.line(48, 14, 48, 74, "accent", SW_MARK)
    d.line(52, y, 80, y, "mute", SW_HAIR, extra=DASH_OPEN)     # no head: unlike R12, nothing goes on


def g_universe(d):
    """R2: a member that later left is a ring, but it stays in the grid."""
    for c in range(4):
        for r in range(4):
            x, y = 10 + 20 * c, 10 + 20 * r
            if (c, r) == (2, 1):
                d.circle(x, y, R - SW_MARK / 2, "accent", stroke=True, sw=SW_MARK)    # outer edge = R
            else:
                d.circle(x, y, R, "ink")


def _branch(sign, a=7):
    pts = [(40 + u, 40 + sign * math.sqrt(u * u + a * a)) for u in range(-35, 36)]
    return "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts)


def g_identity(d):
    """R3: two securities come close (one ticker) but their lines are never joined."""
    d.path(_branch(-1), "ink", SW_MARK)
    d.path(_branch(1), "ink", SW_MARK)
    d.line(31, 40, 49, 40, "accent", SW_MARK)


def g_disappearance(d):
    """R4: a held long that fails, or leaves for an unknown cause, falls to the floor, −100%."""
    floor = 66
    d.line(0, floor, 80, floor, "mute", SW_HAIR)
    for x in HATCH:
        d.line(x, floor + 8, x + 6, floor + 1, "mute", SW_HAIR)
    v = walk(8, seed=21, sigma=0.03, drift=0.004)
    lo, hi = min(v), max(v)
    pts = [(2 + 7.5 * i, 44 - 30 * (u - lo) / (hi - lo)) for i, u in enumerate(v)]
    d.path("M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts), "ink", SW_MARK)
    x, y = pts[-1]
    d.line(x, y, x, floor - 0.5, "accent", SW_MARK)


def _curve(x):
    return 72 - 36 * ((x - 2) / 76) ** 1.4


def g_basis(d):
    """R5: one total-return line; the copy that adds the dividends again is refused (dashed)."""
    xs = list(range(2, 79))
    steps, rise = (26, 52), 10
    first = steps[0]
    ghost = []
    for x in xs:
        if x < first:
            continue
        k = sum(x >= j for j in steps)
        if x in steps and x != first:
            ghost.append((x, _curve(x) - rise * (k - 1)))
        ghost.append((x, _curve(x) - rise * k))
    d.path("M" + " L".join(f"{x} {y:.2f}" for x, y in ghost), "mute", SW_MARK, extra=DASH_OPEN)
    d.path("M" + " L".join(f"{x} {_curve(x):.2f}" for x in xs), "ink", SW_MARK)
    d.line(first, _curve(first), first, _curve(first) - rise, "accent", SW_MARK)


def g_missing(d):
    """R6: a missing value stays a typed blank, and every window that touches it is blanked too."""
    top, bot = 6, 22               # five square 16 px cells; the outer stroke stays inside the box
    edges = [0.75, 16, 32, 48, 64, 79.25]
    d.path(f"M{edges[0]} {top} H{edges[-1]} V{bot} H{edges[0]} Z", "ink", SW_MARK)
    for x in edges[1:-1]:
        d.line(x, top, x, bot, "ink", SW_HAIR)
    cy = (top + bot) / 2
    for i in range(5):
        cx = 8 + 16 * i
        if i == 2:
            d.line(cx - 4, cy - 4, cx + 4, cy + 4, "accent", SW_MARK)
            d.line(cx + 4, cy - 4, cx - 4, cy + 4, "accent", SW_MARK)
        else:
            d.circle(cx, cy, R, "ink")
    # two-cell windows: valid, blanked (touches the x), valid
    for (a, b), y, blank in (((0, 2), 42, False), ((1, 3), 56, True), ((3, 5), 70, False)):
        x1, x2 = edges[a], edges[b]
        cls = "mute" if blank else "ink"
        d.line(x1, y, x2, y, cls, SW_MARK, extra=DASH_OPEN if blank else "")
        d.line(x1, y - 4, x1, y + 4, cls, SW_MARK)
        d.line(x2, y - 4, x2, y + 4, cls, SW_MARK)


def g_volume(d):
    """R7: at a split the price halves and the volume doubles; price x volume is two equal cells on each side."""
    g = 74
    d.line(0, g, 80, g, "mute", SW_HAIR)
    d.path(f"M2 {g} V24 H22 V{g}", "ink", SW_MARK)
    d.line(2, 49, 22, 49, "mute", SW_HAIR)
    d.path(f"M38 {g} V49 H78 V{g}", "ink", SW_MARK)
    d.line(58, 49, 58, g, "mute", SW_HAIR)
    d.line(30, g - 8, 30, g + 6, "accent", SW_MARK)


def g_costs(d):
    """R8: the cost is cut from the top of the result before it is shown."""
    g = 74
    d.line(0, g, 80, g, "mute", SW_HAIR)
    d.rect(22, 16, 36, 18, "accentwash")
    d.path("M22 34 V16 H58 V34", "accent", SW_MARK, extra=DASH_OPEN)
    d.path(f"M22 {g} V34 H58 V{g}", "ink", SW_MARK)


def g_trials(d):
    """R9: every run is a line in the ledger, and the ledger is locked."""
    for y in range(12, 69, 14):
        d.line(0, y, 5, y, "mute", SW_MARK)
        d.line(11, y, 50, y, "ink", SW_MARK)
    d.path("M61 55 V49 A6 6 0 0 1 73 49 V55", "accent", SW_MARK)
    d.path("M58 55 H76 V69 H58 Z", "accent", SW_MARK)


def g_claims(d):
    """R10: the estimate and its interval stay under the evidence ceiling."""
    c = 14
    for x in HATCH:
        d.line(x, c - 1, x + 6, c - 8, "mute", SW_HAIR)
    d.line(2, c, 78, c, "accent", SW_MARK)
    d.line(40, 22, 40, 70, "ink", SW_MARK)
    d.line(34, 22, 46, 22, "ink", SW_MARK)
    d.line(34, 70, 46, 70, "ink", SW_MARK)
    d.circle(40, 46, R, "ink")


def g_privacy(d):
    """R11: rows never leave the frame; only their sum crosses it, as one public point."""
    ys = (10, 25, 40, 55, 70)
    d.path("M0.5 0.5 H42 V79.5 H0.5 Z", "mute", SW_HAIR, extra=DASH_OPEN)
    for y in ys:
        d.path(f"M10 {y} C 22 {y}, 20 40, 32 40", "mute", SW_HAIR)
        d.circle(10, y, R, "ink")
    disc = 6
    cx = 80 - 0.5 - disc
    d.line(32, 40, cx - disc, 40, "ink", SW_MARK)
    d.circle(cx, 40, disc, "ink")
    d.circle(32, 40, R, "accent")


def g_trading(d):
    """R12: the arrow toward an order ends at a stop."""
    d.line(4, 40, 50, 40, "ink", SW_MARK)
    arrow_head(d, 57, 40, "right", "ink")
    d.line(68, 20, 68, 60, "accent", SW_WALL)


TILES = (
    ("R1", "timing", g_timing), ("R2", "universe", g_universe), ("R3", "identity", g_identity),
    ("R4", "disappearance", g_disappearance), ("R5", "one return basis", g_basis),
    ("R6", "missing stays blank", g_missing),
    ("R7", "split-safe volume", g_volume), ("R8", "costs", g_costs), ("R9", "every trial counted", g_trials),
    ("R10", "honest claims", g_claims), ("R11", "privacy", g_privacy), ("R12", "no trading", g_trading),
)


def build():
    d = Doc("guards", W, H)
    for i, (rn, label, glyph) in enumerate(TILES):
        row, col = divmod(i, COLS)
        x = X0 + col * CW
        y = TOP + row * ROW
        assert bm.width(label, WORD) <= CW - 12, label     # 12 px clear of the next column
        d.add(f'<g transform="translate({x:.2f} {y:.2f})">')
        glyph(d)
        d.add("</g>")
        base = y + S + NUM_GAP
        d.text(rn, x, base, SIZE_LABEL, "ink", "bold")
        d.text(label, x, base + LINE, WORD, "mute")
    for row in range(2):       # no rule on top: the README heading above already draws one
        ry = TOP + row * ROW + S + NUM_GAP + LINE + RULE_GAP
        d.line(X0, ry, X1, ry, "hair", SW_HAIR)
        for c in range(COLS + 1):
            d.line(X0 + c * CW, ry - 4, X0 + c * CW, ry + 4, "faint", SW_HAIR)
    return d


if __name__ == "__main__":
    build().write()
