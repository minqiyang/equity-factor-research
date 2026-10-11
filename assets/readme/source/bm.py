"""Berkeley Mono text as SVG outline paths, and a headless Chrome preview renderer.

The README images carry the glyph outlines, not the font file, so GitHub shows the same letters everywhere.
"""
from __future__ import annotations

import os
import subprocess
from functools import lru_cache
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

FONT_DIR = Path(os.environ.get("BERKELEY_MONO_DIR", Path.home() / "Library/Fonts"))
FACES = {"regular": "BerkeleyMono-Regular.otf", "bold": "BerkeleyMono-Bold.otf",
         "oblique": "BerkeleyMono-Oblique.otf", "boldoblique": "BerkeleyMono-Bold-Oblique.otf"}
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


@lru_cache(maxsize=None)
def _font(face: str):
    f = TTFont(FONT_DIR / FACES[face])
    return f, f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm, f["hmtx"]


def advance(size: float, face: str = "regular") -> float:
    """Advance width of one glyph (the font is monospaced)."""
    f, gs, cmap, upm, hmtx = _font(face)
    return hmtx[cmap[ord("0")]][0] * size / upm


def width(text: str, size: float, face: str = "regular", track: float = 0.0) -> float:
    return len(text) * (advance(size, face) + track) - (track if text else 0)


def _num(v: float) -> str:
    """Two decimals are enough for type drawn at 13 px or more."""
    t = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if t in ("-0", "") else t


def text_path(text: str, x: float, y: float, size: float, face: str = "regular", anchor: str = "start",
              track: float = 0.0) -> str:
    """SVG path data for ``text`` with its baseline at y. anchor: start, middle, end. track: extra space in px."""
    f, gs, cmap, upm, hmtx = _font(face)
    w = width(text, size, face, track)
    x0 = x - (w / 2 if anchor == "middle" else w if anchor == "end" else 0)
    s = size / upm
    out = []
    cx = x0
    for ch in text:
        gname = cmap.get(ord(ch))
        if gname is None:
            raise ValueError(f"no glyph for {ch!r}")
        if ch != " ":
            pen = SVGPathPen(gs, ntos=_num)
            gs[gname].draw(TransformPen(pen, (s, 0, 0, -s, cx, y)))
            d = pen.getCommands()
            if d:
                out.append(d)
        cx += hmtx[gname][0] * s + track
    return " ".join(out)


def text(t: str, x: float, y: float, size: float, cls: str = "ink", face: str = "regular", anchor: str = "start",
         track: float = 0.0, extra: str = "") -> str:
    d = text_path(t, x, y, size, face, anchor, track)
    return f'<path class="{cls}" d="{d}"{(" " + extra) if extra else ""}/>' if d else ""


def render_png(svg_path: Path, png_path: Path, width_px: int, height_px: int, bg: str, scale: float = 2.0) -> None:
    """Preview: render the SVG on a page with the given background, at device scale ``scale``."""
    png_path = png_path.resolve()
    html = png_path.with_suffix(".html")
    html.write_text(f'<!doctype html><html><body style="margin:0;background:{bg}">'
                    f'<img src="{svg_path.resolve().as_uri()}" style="display:block;width:{width_px}px;height:{height_px}px">'
                    "</body></html>")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    f"--force-device-scale-factor={scale}", f"--window-size={width_px},{height_px}",
                    f"--screenshot={png_path}", html.as_uri()], check=True, capture_output=True, timeout=120)
    html.unlink()
