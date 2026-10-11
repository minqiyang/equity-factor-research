"""Verdict: where the confirm-period edge over SPY came from (reports/m55_confirm_v1.md, OI-09 table).

Primary loader run, primary cost, annual means in percent: CW-PIT - SPY 0.410, TILT - CW-PIT -0.112,
TILT - SPY 0.298. Stop floor 0.300.
"""
from art import SIZE_LABEL, SIZE_NOTE, SIZE_VALUE, Doc

W, H = 1200, 400
X0, X1 = 320, 1157          # axis span; the +0.410 label ends at the 1152 frame
VMIN, VMAX = 0.0, 0.45
ROW = (136, 216, 296)       # bar centres
BH = 32


def vx(v: float) -> float:
    return X0 + (v - VMIN) / (VMAX - VMIN) * (X1 - X0)


def build():
    d = Doc("verdict", W, H)
    gap, tilt, total, floor = 0.410, -0.112, 0.298, 0.300
    top, bot = ROW[0] - BH / 2 - 16, ROW[2] + BH / 2 + 16
    # zero line and ticks
    d.line(vx(0), top, vx(0), bot, "mute", 1)
    for v, lab in ((0.0, "0"), (0.1, "0.1"), (0.2, "0.2"), (0.4, "0.4")):
        d.line(vx(v), bot, vx(v), bot + 6, "mute", 1)
        d.text(lab, vx(v), bot + 28, SIZE_NOTE, "mute", anchor="middle")
    # a waterfall from SPY to the tilted book
    d.rect(vx(0), ROW[0] - BH / 2, vx(gap) - vx(0), BH, "faint")
    d.rect(vx(gap + tilt), ROW[1] - BH / 2, vx(gap) - vx(gap + tilt), BH, "wash")
    d.path(f"M{vx(gap + tilt):.2f} {ROW[1] - BH / 2 + 0.75:.2f}H{vx(gap) - 0.75:.2f}V{ROW[1] + BH / 2 - 0.75:.2f}"
           f"H{vx(gap + tilt):.2f}Z", "ink", 1.5)
    d.line(vx(gap), ROW[0] + BH / 2, vx(gap), ROW[1] - BH / 2, "mute", 1, 'stroke-dasharray="2 3"')
    d.rect(vx(0), ROW[2] - BH / 2, vx(total) - vx(0), BH, "ink")
    d.line(vx(total), ROW[1] + BH / 2, vx(total), ROW[2] - BH / 2, "mute", 1, 'stroke-dasharray="2 3"')
    # the stop floor: the one place a rule bites
    d.line(vx(floor), top - 16, vx(floor), bot, "accent", 2)
    d.text("stop floor 0.300", vx(floor) + 10, top - 4, SIZE_LABEL, "accent")
    # row labels and values
    labels = (("our index", "vs SPY", "+0.410"), ("factor tilt", "vs our index", "−0.112"),
              ("tilted book", "vs SPY", "+0.298"))
    for (a, b, s), y in zip(labels, ROW):
        d.text(a, 48, y - 2, SIZE_LABEL, "ink")
        d.text(b, 48, y + 18, SIZE_NOTE, "mute")
    d.text("+0.410", vx(gap) + 12, ROW[0] + 6, SIZE_VALUE, "ink", "bold")
    d.text("−0.112", vx(gap + tilt) - 12, ROW[1] + 6, SIZE_VALUE, "ink", "bold", anchor="end")
    d.text("+0.298", vx(total) - 12, ROW[2] + 6, SIZE_VALUE, "slab", "bold", anchor="end")
    d.text("confirm 1993-2014, % a year after costs", 48, 50, SIZE_NOTE, "mute")
    return d


if __name__ == "__main__":
    build().write()
