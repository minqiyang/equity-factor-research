"""Timing (R1): after_close_signal_next_observed_close_v1 at a month-end rebalance row r."""
from art import (DASH_OPEN, MARGIN, SIZE_LABEL, SIZE_NOTE, SW_HAIR, SW_MARK, SW_WALL, Doc, arrow_head)

W, H = 1200, 184
DAYS = ["r−4", "r−3", "r−2", "r−1", "r", "r+1", "r+2", "r+3"]
R = DAYS.index("r")
PITCH, CELL = 140, 124          # 7 * 140 + 124 = 1104 = 1152 - 48; 124 and 28 are 8k + 4, so dashes meet the corners
Y, CH = 88, 28                  # the row of daily cells
Y_LABEL, Y_SPAN, Y_TICK = 52, 72, 140


def cx(i: int) -> float:
    return MARGIN + i * PITCH


def build():
    d = Doc("timing", W, H)
    for i, lab in enumerate(DAYS):
        x = cx(i)
        if i < R:                                         # known: read by the model
            d.rect(x, Y, CELL, CH, "ink")
        elif i == R:                                      # the trade row: not read; its close is the trade price
            d.rect(x, Y, CELL, CH, "wash")
            h = SW_MARK / 2
            d.path(f"M{x + h} {Y + h}H{x + CELL}M{x + h} {Y + h}V{Y + CH - h}H{x + CELL}", "faint", SW_MARK)
        else:                                             # future: not read
            for x1, y1, x2, y2 in ((x, Y, x + CELL, Y), (x + CELL, Y, x + CELL, Y + CH),
                                   (x, Y + CH, x + CELL, Y + CH), (x, Y, x, Y + CH)):
                d.line(x1, y1, x2, y2, "faint", SW_MARK, DASH_OPEN)
        d.text(lab, x + CELL / 2, Y_TICK, SIZE_NOTE, "mute", anchor="middle")

    # what the model reads: rows up to r-1
    xa, xb = cx(0), cx(R - 1) + CELL
    d.line(xa, Y_SPAN, xb, Y_SPAN, "mute", SW_HAIR)
    d.line(xa + 0.5, Y_SPAN, xa + 0.5, Y_SPAN + 6, "mute", SW_HAIR)
    d.line(xb - 0.5, Y_SPAN, xb - 0.5, Y_SPAN + 6, "mute", SW_HAIR)
    d.text("scores, weights, risk: known by r−1", xa, Y_LABEL, SIZE_LABEL, "ink")

    # the trade: one wall at the close of row r
    xw = cx(R) + CELL
    d.line(xw, Y_SPAN - 8, xw, Y + CH + 8, "accent", SW_WALL)
    d.text("trade at the close", xw, Y_LABEL, SIZE_LABEL, "accent", anchor="middle")

    # the return starts at that close, so it counts from row r+1
    xe = cx(len(DAYS) - 1) + CELL
    d.line(xw + SW_WALL / 2, Y_SPAN, xe - 6, Y_SPAN, "mute", SW_HAIR)
    arrow_head(d, xe, Y_SPAN, "right", "mute")
    d.text("return counts from r+1", xe, Y_LABEL, SIZE_LABEL, "ink", anchor="end")
    return d


if __name__ == "__main__":
    build().write()
