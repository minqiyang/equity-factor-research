"""Draw every README image in both themes.

    python build.py                 # writes assets/readme/<name>-light.svg and <name>-dark.svg
    python build.py --png /tmp/png  # also writes PNG previews (needs Google Chrome)
"""
import argparse
import importlib
from pathlib import Path

import art

IMAGES = ("hero", "timing", "chain", "verdict", "screen", "guards", "ledger", "process", "tilt", "exits", "blanks",
          "journey")


def main() -> None:
    ap = argparse.ArgumentParser(description="Draw the README images.")
    ap.add_argument("--out", type=Path, default=art.OUT, help="folder for the SVG files")
    ap.add_argument("--png", type=Path, help="also write PNG previews to this folder")
    a = ap.parse_args()
    for name in IMAGES:
        importlib.import_module(name).build().write(a.out, a.png)


if __name__ == "__main__":
    main()
