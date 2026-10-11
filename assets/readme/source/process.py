"""Process: how a change gets into the repository. Eight stations on one track, three gates that cannot be skipped,
and one return lane: a failed review goes back to build; after 2 failures a stronger setup takes over, and after
2 more the owner decides (docs/codex_long_running_controller.md, escalation rule)."""
from art import (MARGIN, SIZE_LABEL, SIZE_NOTE, SW_HAIR, SW_WALL, Doc, arrow_head)

W, H = 1200, 280
T = 144                                   # the track
NODE = 10                                 # stage nodes are 10 px squares
STATIONS = (("owner goal", ""), ("design note", "2 pages max"), ("rules frozen", "before any result"),
            ("build", "synthetic data"), ("QA", "full suite"), ("review", "1 or 2 seats"), ("merge", ""),
            ("records", ""))
# end nodes sit flush with the frame; a gap that holds a gate is wider
X = (MARGIN + NODE / 2, 216, 392, 536, 672, 848, 1024, W - MARGIN - NODE / 2)
GATES = ((1, ("2 seats,", "2 model families")), (4, ("clean copy,", "exact head")), (5, ("0 material", "findings")))
XB, XR = X[3], X[5]                       # build, review
LANE = T + 64                             # the return lane
XS = 272                                  # the stronger setup, clear of the gate above it
TAG_Y = (52, 69)                          # two-line gate tags, a flag on the wall
GATE_TOP, GATE_BOT = 42, T + 16       # the wall rises to the top of its tag


def anchor(i: int) -> tuple[float, str]:
    """Inner labels sit centred on their node; the two end labels sit flush with the frame."""
    if i == 0:
        return MARGIN, "start"
    if i == len(X) - 1:
        return W - MARGIN, "end"
    return X[i], "middle"


def build() -> Doc:
    d = Doc("process", W, H)
    d.line(X[0], T, X[-1], T, "ink", SW_HAIR)
    for i, (lab, note) in enumerate(STATIONS):
        d.rect(X[i] - NODE / 2, T - NODE / 2, NODE, NODE, "ink")
        x, anc = anchor(i)
        d.text(lab, x, T - 42, SIZE_LABEL, "ink", anchor=anc)
        if note:
            d.text(note, x, T - 20, SIZE_NOTE, "mute", anchor=anc)
    # gates: a wall across the track in the middle of its gap, the rule it checks as a flag on it
    for i, lines in GATES:
        gx = (X[i] + X[i + 1]) / 2
        d.rect(gx - SW_WALL / 2, GATE_TOP, SW_WALL, GATE_BOT - GATE_TOP, "accent")
        for y, t in zip(TAG_Y, lines):
            d.text(t, gx + SW_WALL / 2 + 8, y, SIZE_NOTE, "mute")
    # fix loop: review -> under the track -> back up into build
    d.path(f"M{XR} {T + NODE / 2}V{LANE}H{XB}V{T + NODE / 2 + 2}", "mute", SW_HAIR)
    arrow_head(d, XB, T + NODE / 2 + 2, "up")
    d.text("fix, new head, review again", (XB + XR) / 2, LANE - 12, SIZE_NOTE, "mute", anchor="middle")
    # escalation: the same lane runs on to the left, through a stronger setup, and up into the owner
    d.line(XB, LANE, XS + NODE / 2 + 2, LANE, "mute", SW_HAIR)
    arrow_head(d, XS + NODE / 2 + 2, LANE, "left")
    d.text("after 2 failures", (XB + XS) / 2, LANE - 12, SIZE_NOTE, "mute", anchor="middle")
    d.rect(XS - NODE / 2, LANE - NODE / 2, NODE, NODE, "mute")
    d.text("stronger setup", XS, LANE + 26, SIZE_LABEL, "mute", anchor="middle")
    d.path(f"M{XS - NODE / 2} {LANE}H{X[0]}V{T + NODE / 2 + 2}", "mute", SW_HAIR)
    arrow_head(d, X[0], T + NODE / 2 + 2, "up")
    d.text("after 2 more", (XS + X[0]) / 2, LANE - 12, SIZE_NOTE, "mute", anchor="middle")
    return d


if __name__ == "__main__":
    build().write()
