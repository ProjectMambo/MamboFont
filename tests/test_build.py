#!/usr/bin/env python3
"""One end-to-end check for the direct-outline MamboFont pilot."""

import re
import sys
import tempfile
from math import hypot
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import fontforge

from script.mbfont import PILOT_CODEPOINTS, WEIGHTS, _without_redundant_points, compile_fonts
from sources.glyphs import PILOT_CHARACTERS, pilot_glyphs
from sources.model import Design, design_for


BOLD_GAP_RASTER = {
    "A": ("..#..", ".###.", ".#.#.", ".#.#.", "#####", "##.##", "##.##", "#...#", "#...#"),
    "B": ("#####", "#####", "#..##", "#..##", "#####", "#...#", "#...#", "#####", "#####"),
    "M": ("##.##", "##.##", "##.##", "#####", "#####", "#...#", "#...#", "#...#", "#...#"),
    "N": ("##..#", "###.#", "###.#", "###.#", "#.#.#", "#.###", "#.###", "#.###", "#..##"),
    "W": ("#...#", "#...#", "#...#", "#...#", "#...#", "#####", "#####", "##.##", "##.##"),
    "a": ("#####", "#####", "....#", "#####", "#...#", "#####"),
    "e": ("#####", "#####", "#....", "#####", "#....", "#####"),
    "m": ("##.##", "##.##", "#####", "#...#", "#...#", "#...#"),
    "0": ("#####", "#####", "#.###", "#.###", "#.#.#", "###.#", "###.#", "#####", "#####"),
}
BOLD_NOTCH_RASTERS = {
    16: {
        "M": ("##..##", "##..##", "######", "######", "######", "######", "##..##", "##..##", "##..##", "##..##"),
        "W": ("##..##", "##..##", "##..##", "##..##", "##..##", "######", "######", "######", "##..##", "##..##"),
        "m": ("##..##", "######", "######", "##..##", "##..##", "##..##"),
    },
    24: {
        "M": ("####..####", "####..####", "####..####", "##########", "##########", "##########", "##########", "##########", "##########", "###....###", "###....###", "###....###", "###....###", "###....###", "###....###"),
        "W": ("###....###", "###....###", "###....###", "###....###", "###....###", "###....###", "###....###", "##########", "##########", "##########", "##########", "##########", "####..####", "####..####", "###....###"),
        "m": ("###....###", "####..####", "##########", "##########", "##########", "###....###", "###....###", "###....###", "###....###", "###....###"),
    },
}
BOLD_GAP_OUTCOMES = {
    "A": "widen",
    "B": "preserve",
    "M": "widen",
    "N": "preserve",
    "W": "widen",
    "a": "widen",
    "e": "widen",
    "m": "widen",
    "0": "preserve",
}


def raster(glyph, directory, ppem):
    path_value = directory / f"u{glyph.unicode:04x}-{ppem}.xbm"
    glyph.export(str(path_value), pixelsize=ppem, bitdepth=1)
    source = path_value.read_text()
    width = int(re.search(r"_width (\d+)", source).group(1))
    height = int(re.search(r"_height (\d+)", source).group(1))
    values = [int(value, 16) for value in re.findall(r"0x([0-9a-fA-F]+)", source)]
    stride = (width + 7) // 8
    rows = [
        [bool(values[y * stride + x // 8] & (1 << (x % 8))) for x in range(width)]
        for y in range(height)
    ]
    black = [(x, y) for y, row in enumerate(rows) for x, value in enumerate(row) if value]
    left, right = min(x for x, _ in black), max(x for x, _ in black)
    top, bottom = min(y for _, y in black), max(y for _, y in black)
    return tuple(
        "".join("#" if rows[y][x] else "." for x in range(left, right + 1))
        for y in range(top, bottom + 1)
    )


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
    resized = Design(
        advance=600,
        ink_left=48,
        ink_right=552,
        ascent=850,
        descent=150,
        cap_height=680,
        x_height=430,
        descender=-120,
    )
    resized_recipes = pilot_glyphs(resized)
    assert tuple(
        sum(point[0] for point in shape[:2]) / 2
        for shape in resized_recipes["A"]["ink"][:2]
    ) == (resized.x("diagonal_left"), resized.x("diagonal_right"))
    assert all(
        0 <= x <= resized.advance and -resized.descent <= y <= resized.ascent
        for blueprint in resized_recipes.values()
        for contour in (*blueprint["ink"], *blueprint["cuts"])
        for x, y in contour
    )
    assert set(PILOT_CHARACTERS) == set(pilot_glyphs(design_for("Regular")))
    topology = None
    for style, _ in WEIGHTS:
        design = design_for(style)
        recipes = pilot_glyphs(design)
        current = {
            char: (len(value["ink"]), len(value["cuts"]), tuple(rule.name for rule in value["gaps"]))
            for char, value in recipes.items()
        }
        topology = current if topology is None else topology
        assert current == topology
        assert all(
            rule.resolved == 0 or rule.resolved >= rule.minimum
            for blueprint in recipes.values()
            for rule in blueprint["gaps"]
        )
        assert all(
            design.ink_left <= x <= design.ink_right
            for char in "MWm"
            for contour in recipes[char]["ink"]
            for x, _ in contour
        )
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
        for char, blueprint in recipes.items():
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
                    if char not in "MWm":
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
        bold = fontforge.open(str(next(path for path in first_files if path.name.startswith("MamboFontPilot-Bold_") and path.suffix == ".ttf")))
        try:
            raster_dir = Path(first) / "raster"
            raster_dir.mkdir()
            assert {
                char: raster(bold[ord(char)], raster_dir, design_for("Bold").review_ppem)
                for char in BOLD_GAP_RASTER
            } == BOLD_GAP_RASTER
            for ppem, expected in BOLD_NOTCH_RASTERS.items():
                assert {
                    char: raster(bold[ord(char)], raster_dir, ppem)
                    for char in expected
                } == expected
        finally:
            bold.close()

        bold_recipes = pilot_glyphs(design_for("Bold"))
        assert {
            char: blueprint["gaps"][0].outcome
            for char, blueprint in bold_recipes.items()
            if blueprint["gaps"]
        } == BOLD_GAP_OUTCOMES
        assert set(BOLD_GAP_RASTER) == set(BOLD_GAP_OUTCOMES)

    print("ok: deterministic direct-outline pilot, 4 weights, TTF + WOFF2")


if __name__ == "__main__":
    main()
