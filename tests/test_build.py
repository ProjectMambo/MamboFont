#!/usr/bin/env python3
"""One end-to-end check for the config-driven direct-outline ASCII pilot."""

import re
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import fontforge

from script.mbfont import (
    ASCII_CHARACTERS,
    _without_redundant_points,
    compile_fonts,
    encoded_codepoints,
    weights,
)
from sources.config import blueprint_for, load_project


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


def raster(glyph, directory, ppem):
    path = directory / f"u{glyph.unicode:04x}-{ppem}.xbm"
    glyph.export(str(path), pixelsize=ppem, bitdepth=1)
    source = path.read_text()
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


def inspect(path, project):
    font = fontforge.open(str(path))
    try:
        encoded = {item.unicode for item in font.glyphs() if item.unicode >= 0}
        family = project.font["family"]
        metrics = project.font["metrics"]
        assert font.validate(True) == 0, path
        assert encoded == encoded_codepoints(project), path
        assert font.familyname == family["name"], path
        assert font.copyright == family["copyright"], path
        assert font.os2_panose[3] == 9, path
        assert (font.hhea_ascent, font.hhea_descent, font.hhea_linegap) == (
            metrics["ascent"], -metrics["descent"], 0,
        ), path
        for item in font.glyphs():
            is_ours = item.unicode >= 0 or item.glyphname == ".notdef"
            if is_ours:
                assert item.width == metrics["advance"], (path, item.glyphname)
                assert all(point.on_curve for contour in item.foreground for point in contour)
                assert all(
                    point.x == round(point.x) and point.y == round(point.y)
                    for contour in item.foreground for point in contour
                )
                assert all(
                    points == _without_redundant_points(points)
                    for contour in item.foreground
                    if (points := [(point.x, point.y) for point in contour])
                ), (path, item.glyphname)
            if item.unicode >= 0:
                left, bottom, right, top = item.boundingBox()
                assert 0 <= left <= right <= metrics["advance"], (path, item.glyphname)
                assert -metrics["descent"] <= bottom <= top <= metrics["ascent"], (path, item.glyphname)
        assert all(not font[codepoint].foreground for codepoint in project.empty)
    finally:
        font.close()


def main():
    assert _without_redundant_points(
        [(0, 0), (0, 0), (1, 0), (2, 0), (2, 2), (0, 2)]
    ) == [(0, 0), (2, 0), (2, 2), (0, 2)]

    project = load_project()
    assert len(encoded_codepoints(project)) == 161
    assert set(map(ord, ASCII_CHARACTERS)) <= encoded_codepoints(project)
    for style, _ in weights(project):
        assert all(
            blueprint_for(project, f"U+{ord(char):04X}", style)["ink"]
            for char in ASCII_CHARACTERS
        )

    active_python = [*(ROOT / "sources").glob("*.py"), *(ROOT / "script").glob("*.py")]
    assert all(".stroke(" not in path.read_text() for path in active_python)

    with tempfile.TemporaryDirectory(prefix="mambofont-test-a.") as first, tempfile.TemporaryDirectory(prefix="mambofont-test-b.") as second:
        first_files = compile_fonts("0.0.0", Path(first), ("ttf", "woff2"))
        second_files = compile_fonts("0.0.0", Path(second), ("ttf", "woff2"))
        assert len(first_files) == len(weights(project)) * 2
        assert [item.name for item in first_files] == [item.name for item in second_files]
        for left, right in zip(first_files, second_files):
            assert left.read_bytes() == right.read_bytes(), left.name
            inspect(left, project)

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

    print("ok: deterministic JSON ASCII + empty controls, 4 weights, TTF + WOFF2")


if __name__ == "__main__":
    main()
