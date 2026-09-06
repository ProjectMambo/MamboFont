#!/usr/bin/env python3
"""Small end-to-end contract check for the generated font."""

import sys
import tempfile
from string import ascii_letters, digits
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import fontforge

from script.mbfont import WEIGHTS, compile_fonts
from sources import text


def encoded(font):
    return {item.unicode for item in font.glyphs() if item.unicode >= 0}


def inspect(path_value, expected, advance):
    font = fontforge.open(str(path_value))
    try:
        assert font.validate(True) == 0, path_value
        assert encoded(font) == expected, path_value
        assert all(item.width == advance for item in font.glyphs() if item.unicode >= 0), path_value
        assert (font.hhea_ascent, font.hhea_descent, font.hhea_linegap) == (900, -200, 0), path_value
        assert (font.os2_winascent, font.os2_windescent) == (900, 200), path_value
        assert all(0 <= item.boundingBox()[0] and item.boundingBox()[2] <= advance for item in font.glyphs() if item.unicode >= 0), path_value
        assert font.copyright == "Copyright (c) 2026 ProjectMambo"
        if advance == 500:
            assert font.os2_panose[3] == 9, path_value
    finally:
        font.close()


def main():
    text_points = set(text.TARGET_CODEPOINTS)
    assert len(text_points) == 218
    for char in ascii_letters + digits:
        for points in text.GLYPHS[char]["paths"]:
            for (left_x, left_y), (right_x, right_y) in zip(points, points[1:]):
                dx, dy = abs(right_x - left_x), abs(right_y - left_y)
                assert not (dx and dy) or max(dx, dy) > 100, (char, (left_x, left_y), (right_x, right_y))

    with tempfile.TemporaryDirectory(prefix="mambofont-test-a.") as first, tempfile.TemporaryDirectory(prefix="mambofont-test-b.") as second:
        first_files = compile_fonts("0.0.0", Path(first), ("ttf", "woff2"))
        second_files = compile_fonts("0.0.0", Path(second), ("ttf", "woff2"))
        assert len(first_files) == len(WEIGHTS) * 2
        assert [item.name for item in first_files] == [item.name for item in second_files]
        for left, right in zip(first_files, second_files):
            assert left.read_bytes() == right.read_bytes(), left.name
            inspect(left, text_points, 500)

    print("ok: deterministic 4-weight MamboFont build")


if __name__ == "__main__":
    main()
