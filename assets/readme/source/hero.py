"""Hero: every month of the study as one hairline, 1963-07 to 2025-11."""
from art import Doc

W, H = 1600, 560
L, R = 96, 1504
TOP, BOT = 240, 432


def months(a: tuple[int, int], b: tuple[int, int]):
    y, m = a
    while (y, m) <= b:
        yield y, m
        m += 1
        if m == 13:
            y, m = y + 1, 1


ALL = list(months((1963, 7), (2025, 11)))
SCREEN = ((1963, 7), (1992, 12))
CONFIRM = ((1993, 2), (2014, 3))
CHECK = ((2014, 4), (2025, 11))
SEAL = ((2019, 7), (2020, 7))      # the sealed year, never read
GAP = ((2020, 8), (2021, 8))       # left out of the check: the sealed row and the 252-row warm-up


def inside(ym, span):
    return span[0] <= ym <= span[1]


def build():
    d = Doc("hero", W, H, slab=True)
    step = (R - L) / (len(ALL) - 1)
    x = {ym: L + i * step for i, ym in enumerate(ALL)}
    # the sealed year: a solid block, no month inside it is drawn
    sx0, sx1 = x[SEAL[0]] - step / 2, x[SEAL[1]] + step / 2
    d.rect(sx0, TOP, sx1 - sx0, BOT - TOP, "accent")
    def cls_of(ym):
        if inside(ym, SEAL):
            return None                 # drawn above as one solid block
        if inside(ym, SCREEN):
            return "faint"
        if (inside(ym, CONFIRM) or inside(ym, CHECK)) and not inside(ym, GAP):
            return "ink"
        return "hair"                   # in no period: 1993-01 and the warm-up after the seal
    # runs of months that share a class become one block
    run = [ALL[0]]
    for ym in ALL[1:] + [None]:
        if ym is not None and cls_of(ym) == cls_of(run[0]):
            run.append(ym)
            continue
        if cls_of(run[0]):
            x0, x1 = x[run[0]] - step / 2, x[run[-1]] + step / 2
            d.rect(x0, TOP, x1 - x0, BOT - TOP, cls_of(run[0]))
        run = [ym]
    # a ruler under the field: one tick a year, a longer tick and a label each decade
    for ym in ALL:
        if ym[1] == 1:
            decade = ym[0] % 10 == 0
            d.line(x[ym] - step / 2, BOT + 10, x[ym] - step / 2, BOT + (24 if decade else 16), "mute", 1)
            if decade and ym[0] != 2020:
                d.text(str(ym[0]), x[ym] - step / 2, BOT + 52, 18, "mute", anchor="middle")
    for xe, lab, anc in ((x[ALL[0]] - step / 2, "1963", "start"), (x[ALL[-1]] + step / 2, "2025", "end")):
        d.line(xe, BOT + 10, xe, BOT + 24, "ink", 1)
        d.text(lab, xe, BOT + 52, 18, "ink", anchor=anc)
    d.text("sealed", (sx0 + sx1) / 2, BOT + 52, 18, "accent", anchor="middle")
    # each period as a span above the field
    for span, name in ((SCREEN, "screen"), (CONFIRM, "confirm"), (CHECK, "check")):
        x0, x1 = x[span[0]] - step / 2 + 1, x[span[1]] + step / 2 - 1
        d.path(f"M{x0:.2f} {TOP - 8}V{TOP - 16}H{x1:.2f}V{TOP - 8}", "mute", 1)
        d.text(name, x0, TOP - 28, 18, "mute")
    # title block
    d.text("equity factor research", L, 120, 56, "ink", "bold")
    d.text("749 months of US stocks, every input known before the trade", L, 164, 22, "mute")
    return d


if __name__ == "__main__":
    build().write()
