# README images

These scripts draw every image in `assets/readme/`. Each module draws one image, in a light and a dark theme, from
one drawing. The numbers in the images come from the tracked reports `reports/m55_screen_v1.md` and
`reports/m55_confirm_v1.md`. Each module names its source.

The text is Berkeley Mono. The scripts convert each glyph to an outline path, so the SVG files hold no font file
and show the same letters on every machine.

To rebuild, you need Python 3.11, `fonttools`, and a licensed copy of Berkeley Mono. Set `BERKELEY_MONO_DIR` when
the `.otf` files are not in `~/Library/Fonts`.

```bash
python -m pip install fonttools
python build.py                    # writes the SVG files to assets/readme/
python build.py --png /tmp/readme  # also writes PNG previews, with Google Chrome
```
