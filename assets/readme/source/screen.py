"""Screen: what the screen picked versus what happened next (M5.5, primary loader run, primary cost).

x: screen information ratio against CW-PIT, over screen months up to 1992-12 (S2 and S3 have 36, from 1990-01).
y: confirm-period active return against CW-PIT, percent a year, 1993-02 to 2014-03. Shortlist rule: IR >= 0.2 and
HAC t >= 1.0; only S3 and S4 passed (S2 has IR 0.341 but screen t 0.626). S5 had no screen value
(screen_too_short). Smallest secondary-family q is 0.9337 (S7).
Sources: reports/m55_screen_v1.md (primary, primary rows) and reports/m55_confirm_v1.md (secondary family).
"""
from art import DASH_LEADER, MARGIN, SIZE_LABEL, SIZE_NOTE, SIZE_VALUE, SW_HAIR, SW_MARK, Doc

W, H = 1200, 504
SX0, SX1 = 96, 216              # strip for the candidate with no screen value
PX0, PX1 = 256, 1140            # main plot, screen IR
XMIN, XMAX = -0.4, 1.2
PY0, PY1 = 88, 408              # plot top (0.6) and bottom (-0.4)
YMIN, YMAX = -0.4, 0.6
TICK = 6
R_DOT, R_PICK = 3.5, 6.0
CAP = 0.68                      # cap height of Berkeley Mono, in em

POINTS = {"S1": (-0.173, -0.066), "S2": (0.341, 0.199), "S3": (1.104, -0.287), "S4": (0.686, 0.031),
          "S6": (0.039, 0.209), "S7": (0.043, 0.519), "S8": (-0.320, 0.054)}
PICKED = ("S3", "S4")
S5_Y = 0.082
THRESHOLD = 0.2


def vx(v: float) -> float:
    return PX0 + (v - XMIN) / (XMAX - XMIN) * (PX1 - PX0)


def vy(v: float) -> float:
    return PY1 - (v - YMIN) / (YMAX - YMIN) * (PY1 - PY0)


def num(v: float) -> str:
    """Tick text with a real minus sign."""
    return "0" if v == 0 else f"{v:.1f}".replace("-", "−")


def mid(y: float, size: float) -> float:
    """Baseline that centres the cap height of a line of text on y."""
    return y + size * CAP / 2


def hollow(d: Doc, cx: float, cy: float, ground: str) -> None:
    """An open circle filled with the ground it sits on, so no line shows through."""
    d.circle(cx, cy, R_DOT, ground)
    d.circle(cx, cy, R_DOT, "ink", stroke=True, sw=SW_MARK)


def build():
    d = Doc("screen", W, H)
    y0 = vy(0)

    # below zero: the candidate did worse than our own index
    for a, b in ((SX0, SX1), (PX0, PX1)):
        d.rect(a, y0, b - a, PY1 - y0, "wash")
        d.line(a, y0, b, y0, "ink", SW_HAIR)

    # y axis: one hairline with short outward ticks
    d.line(SX0, PY0, SX0, PY1, "mute", SW_HAIR)
    for v in (-0.4, -0.2, 0.0, 0.2, 0.4, 0.6):
        d.line(SX0 - TICK, vy(v), SX0, vy(v), "mute", SW_HAIR)
        d.text(num(v), SX0 - TICK - 6, mid(vy(v), SIZE_NOTE), SIZE_NOTE, "mute", anchor="end")

    # x axis, broken between the strip and the plot
    for a, b in ((SX0, SX1), (PX0, PX1)):
        d.line(a, PY1, b, PY1, "mute", SW_HAIR)
    for xb in (SX1 + 16, SX1 + 24):
        d.line(xb - 4, PY1 + 6, xb + 4, PY1 - 6, "mute", SW_HAIR)
    ytick = PY1 + TICK + 8 + SIZE_NOTE * CAP
    for v in (-0.2, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2):
        d.line(vx(v), PY1, vx(v), PY1 + TICK, "mute", SW_HAIR)
        d.text(num(v), vx(v), ytick, SIZE_NOTE, "mute", anchor="middle")
    d.text("no screen data", (SX0 + SX1) / 2, ytick, SIZE_NOTE, "mute", anchor="middle")

    # the screen's pass mark, both halves of the rule, so S2 reads as a failure and not as an error
    xt = vx(THRESHOLD)
    d.line(xt, PY0, xt, PY1, "mute", SW_MARK, DASH_LEADER)
    d.text("IR ≥ 0.2 and t ≥ 1", xt + 10, mid(PY0, SIZE_LABEL), SIZE_LABEL, "mute")

    # candidates the screen did not pick
    for sid, (x, y) in POINTS.items():
        if sid in PICKED:
            continue
        cx, cy = vx(x), vy(y)
        hollow(d, cx, cy, "wash" if y < 0 else "page")
        d.text(sid, cx + 10, mid(cy, SIZE_LABEL), SIZE_LABEL, "mute")
    cx2, cy2 = vx(POINTS["S2"][0]), vy(POINTS["S2"][1])
    d.text("screen t 0.63", cx2 + 10, mid(cy2, SIZE_LABEL) + 18, SIZE_NOTE, "mute")
    s5x = (SX0 + SX1) / 2
    hollow(d, s5x, vy(S5_Y), "page")
    d.text("S5", s5x + 10, mid(vy(S5_Y), SIZE_LABEL), SIZE_LABEL, "mute")

    # the two picks; S3 fell below our index, measured like a dimension from the zero line
    sx, sy = vx(POINTS["S3"][0]), vy(POINTS["S3"][1])
    d.line(sx, y0, sx, sy - R_PICK - 3, "mute", SW_HAIR, DASH_LEADER)
    d.circle(sx, sy, R_PICK, "accent")
    d.text("−0.287", sx - 16, mid((y0 + sy) / 2, SIZE_VALUE), SIZE_VALUE, "ink", "bold", anchor="end")
    d.text("S3 picked", sx - 16, mid(sy, SIZE_LABEL), SIZE_LABEL, "accent", anchor="end")
    fx, fy = vx(POINTS["S4"][0]), vy(POINTS["S4"][1])
    d.circle(fx, fy, R_PICK, "accent")
    d.text("S4 picked", fx, fy - R_PICK - 10, SIZE_LABEL, "accent", anchor="middle")

    # axis titles keep the years, so the reader sees that the two axes use different months
    top = 50                                     # "(" rises 0.748 em, so its top lands on y 40
    d.text("confirm 1993-2014, vs our index, % a year", MARGIN, top, SIZE_NOTE, "mute")
    d.text("none significant after correction (q ≥ 0.93)", PX1, top, SIZE_NOTE, "mute", anchor="end")
    d.text("screen IR, before 1993", PX1, ytick + 26, SIZE_NOTE, "mute", anchor="end")
    return d


if __name__ == "__main__":
    build().write()
