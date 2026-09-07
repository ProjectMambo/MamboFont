#!/usr/bin/env python3
"""One end-to-end check for the direct-outline printable-ASCII pilot."""

import re
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import fontforge

from script.mbfont import (
    ASCII_CODEPOINTS,
    WEIGHTS,
    _draw_blueprint,
    _make_font,
    _without_redundant_points,
    compile_fonts,
)
from sources.config import blueprint_for, load_project
from sources.glyphs import ASCII_CHARACTERS, ascii_glyphs
from sources.model import Design, design_for


SUPPORTED_REVIEW_SIZES = (14, 16, 24)
BOLD_G_RASTERS = {
    14: ("#####", "#####", "#...#", "#...#", "#####", "#####", "....#", "#####", "#####"),
    16: ("######", "######", "##..##", "##..##", "######", "######", "....##", "######", "######"),
    24: (
        "##########", "##########", "##########", "###....###", "###....###",
        "###....###", "###....###", "##########", "##########", "##########",
        ".......###", ".......###", "##########", "##########", "##########",
    ),
}
BOLD_GAP_OUTCOMES = {
    "0": "preserve",
    "@": "widen",
    "A": "fill",
    "B": "preserve",
    "M": "fill",
    "N": "preserve",
    "W": "fill",
    "a": "widen",
    "e": "widen",
    "g": "preserve",
    "j": "preserve",
    "m": "fill",
    "s": "widen",
    "w": "fill",
    "y": "preserve",
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
    cropped = tuple(
        "".join("#" if rows[y][x] else "." for x in range(left, right + 1))
        for y in range(top, bottom + 1)
    )
    return glyph.boundingBox(), cropped


def inspect(path_value):
    font = fontforge.open(str(path_value))
    try:
        encoded = {item.unicode for item in font.glyphs() if item.unicode >= 0}
        assert font.validate(True) == 0, path_value
        assert encoded == ASCII_CODEPOINTS, path_value
        assert font.familyname == "Mambo Font Pilot", path_value
        assert font.copyright == "Copyright (c) 2026 ProjectMambo", path_value
        assert font.os2_panose[3] == 9, path_value
        assert (font.hhea_ascent, font.hhea_descent, font.hhea_linegap) == (800, -200, 0), path_value
        assert (font.os2_winascent, font.os2_windescent) == (800, 200), path_value
        for item in font.glyphs():
            is_ours = item.unicode >= 0 or item.glyphname == ".notdef"
            if is_ours:
                assert item.width == 500, (path_value, item.glyphname)
                assert all(point.on_curve for contour in item.foreground for point in contour)
                assert all(
                    point.x == round(point.x) and point.y == round(point.y)
                    for contour in item.foreground for point in contour
                )
                assert all(
                    points == _without_redundant_points(points)
                    for contour in item.foreground
                    if (points := [(point.x, point.y) for point in contour])
                ), (path_value, item.glyphname)
            if item.unicode >= 0:
                left, bottom, right, top = item.boundingBox()
                assert 0 <= left <= right <= 500, (path_value, item.glyphname, item.boundingBox())
                assert -200 <= bottom <= top <= 800, (path_value, item.glyphname, item.boundingBox())
    finally:
        font.close()


def main():
    assert _without_redundant_points(
        [(0, 0), (0, 0), (1, 0), (2, 0), (2, 2), (0, 2)]
    ) == [(0, 0), (2, 0), (2, 2), (0, 2)]
    try:
        Design(minimum_gap=200)
    except ValueError:
        pass
    else:
        raise AssertionError("an impossible protected gap must fail at the design boundary")

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
    resized_recipes = ascii_glyphs(resized)
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

    project = load_project()
    assert set(ASCII_CHARACTERS) == set(ascii_glyphs(design_for("Regular")))
    for style, _ in WEIGHTS:
        design = design_for(style)
        recipes = ascii_glyphs(design)

        def size(contour):
            xs, ys = zip(*contour)
            return max(xs) - min(xs), max(ys) - min(ys)

        assert all(blueprint["ink"] for blueprint in recipes.values())
        assert all(
            rule.resolved == 0 or rule.resolved >= rule.minimum
            for blueprint in recipes.values()
            for rule in blueprint["gaps"]
        )
        assert all(
            design.ink_left <= x <= design.ink_right
            for char in "MWmw"
            for contour in recipes[char]["ink"]
            for x, _ in contour
        )
        stem_right = design.advance / 2 + design.thickness / 2
        assert max(x for x, _ in recipes["1"]["ink"][0]) <= stem_right
        for char, index in (("!", 1), ("%", 1), ("%", 2), (".", 0), (":", 0),
                            (":", 1), (";", 0), ("?", 4), ("i", 1), ("j", 3)):
            assert size(recipes[char]["ink"][index]) == (design.thickness,) * 2
        for char, index in (("-", 0), ("_", 0), (",", 1)):
            assert size(recipes[char]["ink"][index])[1] == design.thickness
        for char, index in (("[", 0), ("]", 0), (",", 0)):
            assert size(recipes[char]["ink"][index])[0] == design.thickness

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
        five_diagonal = recipes["5"]["ink"][3]
        seven_diagonal = recipes["7"]["ink"][1]
        assert five_diagonal[1][0] == recipes["5"]["ink"][4][1][0]
        assert five_diagonal[2] == (design.ink_right, design.cap_height / 2 - design.thickness / 2)
        assert seven_diagonal[2] == (design.ink_right, design.cap_height - design.thickness)
        assert len(recipes["("]["ink"][0]) == 8 and len(recipes["~"]["ink"]) == 3

        legacy = _make_font(style, project.font["weights"][style]["css"], "0.0.0")
        configured = fontforge.font()
        try:
            for char in "7AHMOa":
                target = configured.createChar(ord(char))
                _draw_blueprint(
                    target, blueprint_for(project, f"U+{ord(char):04X}", style), design
                )
                assert tuple(
                    tuple((point.x, point.y) for point in contour)
                    for contour in target.foreground
                ) == tuple(
                    tuple((point.x, point.y) for point in contour)
                    for contour in legacy[ord(char)].foreground
                ), (style, char)
            target = configured.createChar(-1, ".notdef")
            _draw_blueprint(target, blueprint_for(project, ".notdef", style), design)
            assert tuple(
                tuple((point.x, point.y) for point in contour)
                for contour in target.foreground
            ) == tuple(
                tuple((point.x, point.y) for point in contour)
                for contour in legacy[".notdef"].foreground
            ), (style, ".notdef")
        finally:
            configured.close()
            legacy.close()

    active_python = [*(ROOT / "sources").glob("*.py"), *(ROOT / "script").glob("*.py")]
    assert all(".stroke(" not in path.read_text() for path in active_python)

    with tempfile.TemporaryDirectory(prefix="mambofont-test-a.") as first, tempfile.TemporaryDirectory(prefix="mambofont-test-b.") as second:
        first_files = compile_fonts("0.0.0", Path(first), ("ttf", "woff2"))
        second_files = compile_fonts("0.0.0", Path(second), ("ttf", "woff2"))
        assert len(first_files) == len(WEIGHTS) * 2
        assert [item.name for item in first_files] == [item.name for item in second_files]
        for left, right in zip(first_files, second_files):
            assert left.read_bytes() == right.read_bytes(), left.name
            inspect(left)

        bold = fontforge.open(str(next(
            path for path in first_files
            if path.name.startswith("MamboFontPilot-Bold_") and path.suffix == ".ttf"
        )))
        try:
            raster_dir = Path(first) / "raster"
            raster_dir.mkdir()
            for ppem in SUPPORTED_REVIEW_SIZES:
                signatures = [raster(bold[ord(char)], raster_dir, ppem) for char in ASCII_CHARACTERS]
                assert len(signatures) == len(set(signatures)), f"duplicate Bold glyph raster at {ppem}px"
                assert raster(bold[ord("g")], raster_dir, ppem)[1] == BOLD_G_RASTERS[ppem]
        finally:
            bold.close()

        bold_recipes = ascii_glyphs(design_for("Bold"))
        assert {
            char: blueprint["gaps"][0].outcome
            for char, blueprint in bold_recipes.items()
            if blueprint["gaps"]
        } == BOLD_GAP_OUTCOMES

    print("ok: deterministic direct-outline printable ASCII, 4 weights, TTF + WOFF2")


if __name__ == "__main__":
    main()
