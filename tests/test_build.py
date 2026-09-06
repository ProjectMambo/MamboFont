#!/usr/bin/env python3
"""Small end-to-end contract check for the generated families."""

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import fontforge

from script.mbfont import WEIGHTS, compile_fonts
from sources import icons, text


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
    legacy_names = (
        "audio-0", "audio-100", "audio-25", "audio-50", "audio-75",
        "battery-0", "battery-100", "battery-25", "battery-50", "battery-75",
        "camera-off", "camera-on", "coconut", "cod", "coffee-empty", "coffee-full",
        "cpu", "disk", "headphones-0", "headphones-100", "headphones-25",
        "headphones-50", "headphones-75", "light-0", "light-100", "light-25",
        "light-50", "light-75", "lock", "mambo", "off", "on", "unlock",
    )
    assert icons.ICON_CODEPOINTS == {name: 0xE000 + index for index, name in enumerate(legacy_names)}
    text_points = set(text.TARGET_CODEPOINTS)
    icon_points = {icons.ICON_CODEPOINTS[name] for name in icons.ICONS}
    assert len(text_points) == 218
    assert len(icon_points) == 30
    assert not ({icons.ICON_CODEPOINTS[name] for name in icons.RETIRED} & icon_points)
    assert icons.NEXT_ICON_CODEPOINT > max(icons.ICON_CODEPOINTS.values())

    with tempfile.TemporaryDirectory(prefix="mambofont-test-a.") as first, tempfile.TemporaryDirectory(prefix="mambofont-test-b.") as second:
        first_files = compile_fonts("0.0.0", Path(first), "all", ("ttf", "woff2"))
        second_files = compile_fonts("0.0.0", Path(second), "all", ("ttf", "woff2"))
        assert len(first_files) == (len(WEIGHTS) + 1) * 2
        assert [item.name for item in first_files] == [item.name for item in second_files]
        for left, right in zip(first_files, second_files):
            assert left.read_bytes() == right.read_bytes(), left.name
            if left.name.startswith("MamboIcons"):
                inspect(left, icon_points, 1000)
            else:
                inspect(left, text_points, 500)

    print("ok: deterministic 4-weight text and 1-weight icon build")


if __name__ == "__main__":
    main()
