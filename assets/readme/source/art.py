"""Shared design system for the README art: palette, light and dark variants, SVG assembly."""
from __future__ import annotations

from pathlib import Path

import bm

OUT = Path(__file__).resolve().parent.parent          # assets/readme

# Two themes. Diagrams are transparent and sit on the GitHub page; the hero carries its own slab.
PALETTE = {
    "light": {"page": "#ffffff", "slab": "#f3f1ec", "ink": "#16171a", "mute": "#6e6c66", "faint": "#bdb9ae",
              "hair": "#dcd8ce", "wash": "#ebe8e0", "accent": "#e2492b", "accentwash": "#f6d9d0", "cool": "#2f5f8f",
              "coolwash": "#dbe5ee"},
    "dark": {"page": "#0d1117", "slab": "#0b0d10", "ink": "#ebe8e1", "mute": "#8f8c85", "faint": "#4a4945",
             "hair": "#26282c", "wash": "#171a1f", "accent": "#ff6a42", "accentwash": "#3a1d16", "cool": "#7fa9d6",
             "coolwash": "#16222f"},
}
CLASSES = ("ink", "mute", "faint", "hair", "wash", "accent", "accentwash", "cool", "coolwash", "slab", "page")


def style(theme: str) -> str:
    p = PALETTE[theme]
    fills = "".join(f".{c}{{fill:{p[c]}}}" for c in CLASSES)
    strokes = "".join(f".s-{c}{{stroke:{p[c]};fill:none}}" for c in CLASSES)
    return f"<style>{fills}{strokes}</style>"


class Doc:
    """An SVG drawn once with class names; written in both themes."""

    def __init__(self, name: str, w: int, h: int, slab: bool = False):
        self.name, self.w, self.h, self.slab = name, w, h, slab
        self.items: list[str] = []

    def add(self, s: str) -> None:
        if s:
            self.items.append(s)

    # shapes ---------------------------------------------------------------
    def rect(self, x, y, w, h, cls="ink", rx=0, extra=""):
        self.add(f'<rect class="{cls}" x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}"'
                 f'{f" rx={chr(34)}{rx}{chr(34)}" if rx else ""}{(" " + extra) if extra else ""}/>')

    def line(self, x1, y1, x2, y2, cls="ink", sw=1.0, extra=""):
        self.add(f'<line class="s-{cls}" x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
                 f'stroke-width="{sw}"{(" " + extra) if extra else ""}/>')

    def path(self, d, cls="ink", sw=1.0, fill=False, extra=""):
        c = cls if fill else f"s-{cls}"
        self.add(f'<path class="{c}" d="{d}"{"" if fill else f" stroke-width={chr(34)}{sw}{chr(34)}"}'
                 f'{(" " + extra) if extra else ""}/>')

    def circle(self, cx, cy, r, cls="ink", stroke=False, sw=1.0, extra=""):
        c = f"s-{cls}" if stroke else cls
        self.add(f'<circle class="{c}" cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}"'
                 f'{f" stroke-width={chr(34)}{sw}{chr(34)}" if stroke else ""}{(" " + extra) if extra else ""}/>')

    def text(self, t, x, y, size, cls="ink", face="regular", anchor="start", track=0.0):
        self.add(bm.text(t, x, y, size, cls, face, anchor, track))

    # output ---------------------------------------------------------------
    def svg(self, theme: str) -> str:
        bg = f'<rect class="slab" width="{self.w}" height="{self.h}"/>' if self.slab else ""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" '
                f'height="{self.h}" role="img">{style(theme)}{bg}{"".join(self.items)}</svg>\n')

    def write(self, out: Path = OUT, png: Path | None = None) -> list[Path]:
        """Write <name>-light.svg and <name>-dark.svg to ``out``; with ``png``, also PNG previews there."""
        out.mkdir(parents=True, exist_ok=True)
        paths = []
        for theme in PALETTE:
            p = out / f"{self.name}-{theme}.svg"
            p.write_text(self.svg(theme))
            paths.append(p)
            if png:
                png.mkdir(parents=True, exist_ok=True)
                bm.render_png(p, png / f"{self.name}-{theme}.png", self.w, self.h, PALETTE[theme]["page"])
        return paths


# shared marks (set standard v2) ---------------------------------------------
SIZE_NOTE, SIZE_LABEL, SIZE_VALUE = 13, 15, 16     # notes and ticks, labels, bold values
SW_HAIR, SW_MARK, SW_EMPH, SW_WALL = 1.0, 1.5, 2.0, 4.0
DASH_LEADER, DASH_OPEN = 'stroke-dasharray="2 3"', 'stroke-dasharray="4 4"'
MARGIN = 48


def arrow_head(d: Doc, x: float, y: float, direction: str = "right", cls: str = "mute") -> None:
    """A solid head, 7 long and 6 wide, with its tip at (x, y)."""
    pts = {"right": ((x - 7, y - 3), (x - 7, y + 3)), "left": ((x + 7, y - 3), (x + 7, y + 3)),
           "down": ((x - 3, y - 7), (x + 3, y - 7)), "up": ((x - 3, y + 7), (x + 3, y + 7))}[direction]
    (ax, ay), (bx, by) = pts
    d.path(f"M{x:.2f} {y:.2f}L{ax:.2f} {ay:.2f}L{bx:.2f} {by:.2f}Z", cls, fill=True)


def walk(n: int, seed: int = 7, sigma: float = 0.010, drift: float = 0.0015) -> list[float]:
    """A seeded random walk of n log levels, for illustrations only (never data)."""
    import random
    rnd, v, out = random.Random(seed), 0.0, []
    for _ in range(n):
        v += drift + rnd.gauss(0, sigma)
        out.append(v)
    return out


def illustration_tag(d: Doc) -> None:
    """The one place the 'illustration' tag goes: right-aligned at the top margin."""
    d.text("illustration", d.w - MARGIN, 50, SIZE_NOTE, "mute", anchor="end")
