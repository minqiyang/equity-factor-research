"""Chain: the real run of the trial (run 4) as a hash chain of seven stage files and the public report.

First 8 hex chars of the SHA-256 of each stage file: coverage 9ad6b30d, calibration 67a7c56c, look be0c5329,
screen c648b3ed, freeze 98ce15ce, confirm 5645cf4e, check ac8052e0. Shortlist digest at the freeze: 62b2c8af.
Source: reports/m55_confirm_v1.md (run 4 stage files, run 2 freeze digest).
"""
import bm
from art import MARGIN, SIZE_LABEL, SIZE_NOTE, SW_EMPH, SW_HAIR, Doc

W = 1200
STAGES = (("coverage", "9ad6b30d"), ("calibration", "67a7c56c"), ("look", "be0c5329"), ("screen", "c648b3ed"),
          ("freeze", "98ce15ce"), ("confirm", "5645cf4e"), ("check", "ac8052e0"))
LOCK = 4                                   # index of the freeze
REPORT = ("public report", "aggregates only")
NODE = 10                                  # stage nodes: 10 px squares
LEAD = 20                                  # baseline to baseline under a node

# Columns: equal steps; the first name starts at the left margin and the last ends at the right margin.
X0 = MARGIN + bm.width(STAGES[0][0], SIZE_LABEL) / 2
XR = W - MARGIN - bm.width(REPORT[0], SIZE_LABEL) / 2
STEP = round((XR - X0) / len(STAGES))
X0 = round(X0)
X = [X0 + i * STEP for i in range(len(STAGES) + 1)]   # the last column is the report

LABEL_Y = 52                               # bracket notes
BRACKET_Y = LABEL_Y + 12
LINE = BRACKET_Y + 40                      # the chain runs on this y; link digests sit 8 px above it
NAME_Y = LINE + 40
H = 208


def lock(d: Doc, cx: float, cy: float) -> tuple[float, float]:
    """A plain padlock in accent, body centred on (cx, cy). Returns its left and right edges."""
    bw, bh = 28, 22
    x0, y0 = cx - bw / 2, cy - bh / 2
    kr = 3                                 # keyhole, cut out of the body with an even-odd fill
    key = (f"M{cx - kr} {cy - 2}a{kr} {kr} 0 1 1 {2 * kr} 0a{kr} {kr} 0 1 1 {-2 * kr} 0z"
           f"M{cx - 1.25} {cy}h2.5v6h-2.5z")
    d.path(f"M{x0} {y0}h{bw}v{bh}h{-bw}z{key}", "accent", fill=True, extra='fill-rule="evenodd"')
    sw, sh = 16, 13                        # shackle
    d.path(f"M{cx - sw / 2} {y0}v{-sh + sw / 2}a{sw / 2} {sw / 2} 0 0 1 {sw} 0v{sh - sw / 2}", "accent", SW_EMPH)
    return x0, x0 + bw


def build():
    d = Doc("chain", W, H)
    edges = []
    for i, (name, _) in enumerate(STAGES):
        x = X[i]
        if i == LOCK:
            edges.append(lock(d, x, LINE))
        else:
            d.rect(x - NODE / 2, LINE - NODE / 2, NODE, NODE, "ink")
            edges.append((x - NODE / 2, x + NODE / 2))
        d.text(name, x, NAME_Y, SIZE_LABEL, "ink", anchor="middle")
    # the shortlist digest: sealed at the freeze; confirm and check take it as a separate input
    d.text("62b2c8af", X[LOCK], NAME_Y + LEAD, SIZE_NOTE, "accent", anchor="middle")
    # the report: a mute square, an output with no stage file of its own
    xr = X[-1]
    d.rect(xr - NODE / 2, LINE - NODE / 2, NODE, NODE, "mute")
    edges.append((xr - NODE / 2, xr + NODE / 2))
    d.text(REPORT[0], xr, NAME_Y, SIZE_LABEL, "ink", anchor="middle")
    d.text(REPORT[1], xr, NAME_Y + LEAD, SIZE_NOTE, "mute", anchor="middle")
    # links: one unbroken line that touches every node; each link carries the digest of the stage file on its
    # left, the digest the next stage checks before it runs, centred on the column step so the row keeps 144
    for i, ((_, hx), (_, a1), (b0, _)) in enumerate(zip(STAGES, edges, edges[1:])):
        d.line(a1, LINE, b0, LINE, "ink", SW_HAIR)
        d.text(hx, (X[i] + X[i + 1]) / 2, LINE - 8, SIZE_NOTE, "mute", anchor="middle")

    # spans: each bracket runs over the names of its stages
    def half(i: int) -> float:
        return bm.width(STAGES[i][0], SIZE_LABEL) / 2

    for i0, i1, label in ((0, LOCK - 1, "uses no value after 1992"), (LOCK + 1, len(STAGES) - 1, "opened after the lock")):
        xa, xb = X[i0] - half(i0), X[i1] + half(i1)
        d.line(xa, BRACKET_Y, xb, BRACKET_Y, "faint", SW_HAIR)
        d.line(xa, BRACKET_Y - 4, xa, BRACKET_Y + 4, "faint", SW_HAIR)
        d.line(xb, BRACKET_Y - 4, xb, BRACKET_Y + 4, "faint", SW_HAIR)
        d.text(label, xa, LABEL_Y, SIZE_NOTE, "mute")
    return d


if __name__ == "__main__":
    build().write()
