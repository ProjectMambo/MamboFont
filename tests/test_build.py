#!/usr/bin/env python3
"""One end-to-end check for the direct-outline MamboFont pilot."""

import sys
import tempfile
from math import hypot
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import fontforge

from script.mbfont import PILOT_CODEPOINTS, WEIGHTS, _without_redundant_points, compile_fonts
from sources.glyphs import PILOT_CHARACTERS, pilot_glyphs
from sources.model import design_for


def inspect(path_value):
    font = fontforge.open(str(path_value))
    try:
        encoded = {item.unicode for item in font.glyphs() if item.unicode >= 0}
        assert font.validate(True) == 0, path_value
        assert encoded == PILOT_CODEPOINTS, path_value
        assert font.familyname == "Mambo Font Pilot", path_value
        assert font.copyright == "Copyright (c) 2026 ProjectMambo", path_value
        assert font.os2_panose[3] == 9, path_value
        assert (font.hhea_ascent, font.hhea_descent, font.hhea_linegap) == (800, -200, 0), path_value
        assert (font.os2_winascent, font.os2_windescent) == (800, 200), path_value
        signature = {}
        for item in font.glyphs():
            is_ours = item.unicode >= 0 or item.glyphname == ".notdef"
            if is_ours:
                assert item.width == 500, (path_value, item.glyphname)
                assert all(point.on_curve for contour in item.foreground for point in contour), (path_value, item.glyphname)
                assert all(point.x == round(point.x) and point.y == round(point.y) for contour in item.foreground for point in contour), (path_value, item.glyphname)
                assert all(
                    points == _without_redundant_points(points)
                    for contour in item.foreground
                    if (points := [(point.x, point.y) for point in contour])
                ), (path_value, item.glyphname)
            if item.unicode >= 0:
                left, bottom, right, top = item.boundingBox()
                assert 0 <= left <= right <= 500, (path_value, item.glyphname, item.boundingBox())
                assert -200 <= bottom <= top <= 800, (path_value, item.glyphname, item.boundingBox())
                signature[item.unicode] = len(item.foreground)
        return signature
    finally:
        font.close()


def main():
    assert _without_redundant_points(
        [(0, 0), (0, 0), (1, 0), (2, 0), (2, 2), (0, 2)]
    ) == [(0, 0), (2, 0), (2, 2), (0, 2)]
    assert set(PILOT_CHARACTERS) == set(pilot_glyphs(design_for("Regular")))
    topology = None
    for style, _ in WEIGHTS:
        design = design_for(style)
        recipes = pilot_glyphs(design)
        current = {char: (len(value["ink"]), len(value["cuts"])) for char, value in recipes.items()}
        topology = current if topology is None else topology
        assert current == topology
        z_diagonal = recipes["Z"]["ink"][1]
        two_diagonal = recipes["2"]["ink"][2]
        assert (z_diagonal[0], z_diagonal[2]) == (
            (design.ink_left, design.thickness),
            (design.ink_right, design.cap_height - design.thickness),
        )
        assert (two_diagonal[0], two_diagonal[2]) == (
            (design.ink_left, design.thickness),
            (design.ink_right, design.x_height),
        )
        for blueprint in recipes.values():
            for contour in blueprint["ink"]:
                edges = list(zip(contour, (*contour[1:], contour[0])))
                if any(left[0] != right[0] and left[1] != right[1] for left, right in edges):
                    assert len(contour) in (4, 5)
                    bottom_left, bottom_right = contour[:2]
                    top_right, top_left = contour[-2:]
                    assert bottom_left[1] == bottom_right[1]
                    assert top_left[1] == top_right[1]
                    side = (top_left[0] - bottom_left[0], top_left[1] - bottom_left[1])
                    cap = (bottom_right[0] - bottom_left[0], bottom_right[1] - bottom_left[1])
                    measured = abs(side[0] * cap[1] - side[1] * cap[0]) / hypot(*side)
                    assert abs(measured - design.thickness) < 1e-9

    active_python = [*(ROOT / "sources").glob("*.py"), *(ROOT / "script").glob("*.py")]
    assert all(".stroke(" not in path.read_text() for path in active_python)

    with tempfile.TemporaryDirectory(prefix="mambofont-test-a.") as first, tempfile.TemporaryDirectory(prefix="mambofont-test-b.") as second:
        first_files = compile_fonts("0.0.0", Path(first), ("ttf", "woff2"))
        second_files = compile_fonts("0.0.0", Path(second), ("ttf", "woff2"))
        assert len(first_files) == len(WEIGHTS) * 2
        assert [item.name for item in first_files] == [item.name for item in second_files]
        final_contours = []
        for left, right in zip(first_files, second_files):
            assert left.read_bytes() == right.read_bytes(), left.name
            signature = inspect(left)
            if left.suffix == ".ttf":
                final_contours.append(signature)
        assert all(signature == final_contours[0] for signature in final_contours)

    print("ok: deterministic direct-outline pilot, 4 weights, TTF + WOFF2")


if __name__ == "__main__":
    main()
