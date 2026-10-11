"""Ledger (R9): the append-only record of every run of the M5.5 trial, failed runs included.

Runs 1-4 by the seven hashed stages. Run 1 wrote coverage and calibration, then the coverage stop ended it before
the look (look to check not run). Run 2 froze the shortlist (digest 62b2c8af). Run 3 repeated the freeze and the
confirm stage refused (held stock, no close). Run 4 wrote all seven stages, repeated the digest, and test A was not
met. Amendments 2, 3, 4 came between the runs. A dotted leader carries the digest down the freeze column, through
the amendment rules. Sources: reports/m55_screen_v1.md, reports/m55_confirm_v1.md, docs/decision_log.md.
"""
import bm
from art import DASH_LEADER, MARGIN, SIZE_LABEL, SIZE_NOTE, SW_HAIR, SW_WALL, Doc

W = 1200
STAGES = ("coverage", "calibration", "look", "screen", "freeze", "confirm", "check")
FREEZE = STAGES.index("freeze")
NODE = 10                  # stage nodes: 10 px squares, as in chain.py
PITCH = 104                # column pitch (13 x 8)
CX0 = 216                  # centre of the first column; every centre is on the 8 px grid
HEAD_Y = 56                # baseline of the stage names
MID0, ROWP = 88, 80        # centre line of row 1, row pitch
OUT_X = 888                # outcome column; the longest outcome ends at 1149
DIGEST = "62b2c8af"
SUB_DY = 25                # second line (date, digest) below the centre line
RULE_DY = 48               # amendment rule below the centre line, midway between two rows of text
WALL_DY = 16               # the stop wall runs from mid - 16 to mid + 16

W_, R_, N_ = "written", "refused", "not run"
RUNS = (
    ("run 1", "2026-10-07", (W_, W_, N_, N_, N_, N_, N_), True, "stopped: coverage too low"),
    ("run 2", "2026-10-08", (W_, W_, W_, W_, W_, N_, N_), False, "shortlist frozen"),
    ("run 3", "2026-10-08", (W_, W_, W_, W_, W_, R_, N_), False, "refused: held stock, no close"),
    ("run 4", "2026-10-09/10", (W_,) * 7, False, "test A not met, below floor"),
)
AMENDMENTS = ("amendment 2", "amendment 3", "amendment 4")
H = 400                    # last ink (run 4 date and digest) at y 353, first ink (stage names) at y 45


def cx(i: int) -> float:
    return CX0 + i * PITCH


def node(d: Doc, state: str, x: float, mid: float) -> None:
    x0, y0 = x - NODE / 2, mid - NODE / 2
    if state == N_:
        d.path(f"M{x0 + 0.5} {y0 + 0.5}h{NODE - 1}v{NODE - 1}h{-(NODE - 1)}z", "faint", SW_HAIR)
    else:
        d.rect(x0, y0, NODE, NODE, "accent" if state == R_ else "ink")


def build():
    d = Doc("ledger", W, H)
    for i, name in enumerate(STAGES):
        d.text(name, cx(i), HEAD_Y, SIZE_LABEL, "mute", anchor="middle")
    for r, (run, date, states, stop, outcome) in enumerate(RUNS):
        mid = MID0 + r * ROWP
        base = mid + 5                          # one baseline for the run label and the outcome
        d.text(run, MARGIN, base, SIZE_LABEL, "ink")
        d.text(date, MARGIN, mid + SUB_DY, SIZE_NOTE, "mute")
        last = max(i for i, s in enumerate(states) if s != N_)
        for i, st in enumerate(states):
            node(d, st, cx(i), mid)
        # connectors: ink, from each node to the next node the run reached
        for i in range(last):
            d.line(cx(i) + NODE / 2, mid, cx(i + 1) - NODE / 2, mid, "ink", SW_HAIR)
        if stop:
            # the coverage stop: a wall midway to the next stage; the chain runs into it
            xw = (cx(last) + cx(last + 1)) / 2
            d.line(cx(last) + NODE / 2, mid, xw - SW_WALL / 2, mid, "ink", SW_HAIR)
            d.rect(xw - SW_WALL / 2, mid - WALL_DY, SW_WALL, 2 * WALL_DY, "accent")
        if states[FREEZE] == W_ and r > 0:
            d.text(DIGEST, cx(FREEZE), mid + SUB_DY, SIZE_NOTE, "mute", anchor="middle")
            if r < len(RUNS) - 1:
                # the same digest again in the next run: a leader from this digest to the next freeze node
                d.line(cx(FREEZE), mid + SUB_DY + 5, cx(FREEZE), mid + ROWP - NODE / 2 - 5, "mute", SW_HAIR,
                       DASH_LEADER)
        d.text(outcome, OUT_X, base, SIZE_LABEL, "ink")
        if r < len(AMENDMENTS):
            y = mid + RULE_DY
            d.text(AMENDMENTS[r], MARGIN, y + 4.5, SIZE_NOTE, "mute")
            x0 = 8 * round((MARGIN + bm.width(AMENDMENTS[r], SIZE_NOTE) + 12) / 8)
            d.line(x0, y, cx(len(STAGES) - 1) + NODE / 2, y, "faint", SW_HAIR)
    return d


if __name__ == "__main__":
    build().write()
