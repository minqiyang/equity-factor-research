"""Tilt: how the tilted book is built from the index at one rebalance (an illustration, not data).

Synthetic: 24 names, index weight b_i = 21 / (i + 3) percent (the top of an index, largest first), synthetic
scores c in [-1, 1], chosen so that the tilted weights sum to the index weights (net -0.03 point). Rule from the
trial file: w = b x (1 + 0.5 c), then |w - b| <= 1 point per stock.

Marks: a faint bar for b; an ink cap at w on every name (above the bar for an up-tilt, across it for a down-tilt).
Where the cap binds, a 1 px mute outline shows the band b +/- 1 point, the ink cap sits on its edge, and a dashed
box from that edge to the raw value b x (1 + 0.5 c) shows the part of the tilt that the cap refused. No stem joins
b and w, so no mark reads as an error bar. Accent: the four bands, the bracket, and its label only.
"""
import bm
from art import (DASH_LEADER, DASH_OPEN, MARGIN, SIZE_LABEL, SIZE_NOTE, SW_EMPH, SW_HAIR, Doc,
                 illustration_tag)

W, H = 1200, 368
N = 24                             # names
S = (W - 2 * MARGIN) / N           # slot pitch: 46, so the axis runs from x = 48 to x = 1152
BASE = 272                         # baseline y
PT = 26                            # px per percentage point
BW, TW = 12, 24                    # bar width; cap, band, and refused-box width
CAP = 1.0                          # points
FOOT = BASE + 48                   # footer baseline
C = (0.5, -0.6, 0.9, -0.9, 0.4, -0.2, -0.4, 0.7, -0.3, 0.9, -0.7, 0.4,
     0.4, -0.5, -0.5, 0.4, -0.8, 0.4, -0.5, 0.5, -0.6, 0.6, -0.5, -0.7)
FORMULA = "w = b × (1 + 0.5 c)   |w − b| ≤ 1 point   tracking error ≤ 2% a year"


def xc(i: int) -> float:
    return MARGIN + i * S + S / 2


def y(pct: float) -> float:
    return BASE - pct * PT


def weights():
    out = []
    for i, c in enumerate(C):
        b = 21 / (i + 3)
        raw = b * (1 + 0.5 * c)
        w = min(max(raw, b - CAP), b + CAP)
        out.append((b, raw, w, abs(raw - w) > 1e-9))
    return out


def label(d: Doc, text: str, x: float, target_y: float, cls: str) -> None:
    """A label about 40 px above its target, with a leader of about 20 px that stops 5 px short of the mark."""
    base = round((target_y - 36) / 8) * 8
    d.text(text, x - 4, base, SIZE_LABEL, cls)
    d.line(x, base + 8, x, target_y - 5, "mute", SW_HAIR, DASH_LEADER)


def build():
    d = Doc("tilt", W, H)
    rows = weights()
    for i, (b, raw, w, binds) in enumerate(rows):
        x = xc(i)
        d.rect(x - BW / 2, y(b), BW, b * PT, "faint")                       # index weight b
        if binds:
            d.rect(x - TW / 2, y(b + CAP), TW, 2 * CAP * PT, "s-mute", extra=f'stroke-width="{SW_HAIR}"')
            top, bot = sorted((y(raw), y(w)))                                     # refused part of the tilt
            d.rect(x - TW / 2, top, TW, bot - top, "s-mute", extra=f'stroke-width="{SW_HAIR}" {DASH_OPEN}')
        d.line(x - TW / 2, y(w), x + TW / 2, y(w), "ink", SW_EMPH)                 # tilted weight w
    d.line(MARGIN, BASE + 0.5, W - MARGIN, BASE + 0.5, "mute", SW_HAIR)

    # the cap: a dimension bracket from b to b + 1 point on the largest name
    b0 = rows[0][0]
    ax = xc(0) + TW / 2 + 8
    d.line(ax, y(b0), ax, y(b0 + CAP), "accent", SW_HAIR)
    for v in (b0, b0 + CAP):
        d.line(ax - 3, y(v), ax + 3, y(v), "accent", SW_HAIR)
    d.text("cap: 1 point per stock", ax + 12, y(b0 + CAP / 2) + 5, SIZE_LABEL, "accent")

    b, raw, w, _ = rows[9]
    label(d, "tilted weight", xc(9), y(w) - 1, "ink")
    b, raw, w, _ = rows[16]
    label(d, "index weight", xc(16), y(b), "mute")

    illustration_tag(d)
    d.text(FORMULA, MARGIN, FOOT, SIZE_NOTE, "mute")
    return d


def check() -> None:
    """Print the facts a reviewer needs: net tilt, smallest move, binding names, label boxes."""
    rows = weights()
    net = sum(w for _, _, w, _ in rows) - sum(b for b, _, _, _ in rows)
    small = min(abs(w - b) * PT for b, _, w, _ in rows)
    print(f"net {net:+.3f} pt, smallest move {small:.1f} px, binds on {[i for i, r in enumerate(rows) if r[3]]}")
    print(f"top ink y {y(max(r[1] for r in rows)):.1f}, marks x {xc(0) - TW / 2:.0f}..{xc(N - 1) + TW / 2:.0f}")
    print(f"cap label box x {xc(0) + TW / 2 + 20:.0f}..{xc(0) + TW / 2 + 20 + bm.width('cap: 1 point per stock', 15):.0f}")


if __name__ == "__main__":
    check()
    build().write()
