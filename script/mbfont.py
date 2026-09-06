#!/usr/bin/env python3
"""Compile the direct-outline MamboFont pilot and its review specimen."""

import argparse
import html
import os
import re
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ["SOURCE_DATE_EPOCH"] = "946684800"

try:
    import fontforge
except ImportError:
    raise SystemExit("FontForge Python bindings are required (run with /usr/bin/python3).")

from sources.glyphs import PILOT_CHARACTERS, pilot_glyphs
from sources.model import Design, design_for, glyph, rectangle


VERSION = "0.4.0"
WEIGHTS = (("Regular", 400), ("Medium", 500), ("SemiBold", 600), ("Bold", 700))
FORMATS = ("ttf", "woff2")
GENERATION_FLAGS = ("opentype", "no-FFTM-table")
PANOSE_WEIGHT = {400: 5, 500: 6, 600: 7, 700: 8}
PILOT_CODEPOINTS = {0x20, *map(ord, PILOT_CHARACTERS)}


def validate_version(value):
    if not re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", value):
        raise argparse.ArgumentTypeError("version must be X.Y.Z")
    return value


def _signed_area(points):
    return sum(
        x1 * y2 - x2 * y1
        for (x1, y1), (x2, y2) in zip(points, (*points[1:], points[0]))
    )


def _add_contour(target, points, clockwise):
    points = tuple(points)
    if (_signed_area(points) < 0) != clockwise:
        points = tuple(reversed(points))
    pen = target.glyphPen(replace=False)
    pen.moveTo(points[0])
    for point in points[1:]:
        pen.lineTo(point)
    pen.closePath()
    del pen


def _without_redundant_points(points):
    cleaned = []
    for point in points:
        if not cleaned or point != cleaned[-1]:
            cleaned.append(point)
    if len(cleaned) > 1 and cleaned[0] == cleaned[-1]:
        cleaned.pop()
    while len(cleaned) >= 3:
        keep = []
        for index, point in enumerate(cleaned):
            before = cleaned[index - 1]
            after = cleaned[(index + 1) % len(cleaned)]
            cross = ((point[0] - before[0]) * (after[1] - point[1])
                     - (point[1] - before[1]) * (after[0] - point[0]))
            forward = ((point[0] - before[0]) * (after[0] - point[0])
                       + (point[1] - before[1]) * (after[1] - point[1]))
            if cross or forward < 0:
                keep.append(point)
        if len(keep) == len(cleaned):
            return cleaned
        cleaned = keep
    return cleaned


def _remove_redundant_points(target):
    width = target.width
    contours = [
        _without_redundant_points([(point.x, point.y) for point in contour])
        for contour in target.foreground
    ]
    pen = target.glyphPen(replace=True)
    for points in contours:
        pen.moveTo(points[0])
        for point in points[1:]:
            pen.lineTo(point)
        pen.closePath()
    del pen
    target.width = width


def _normalize(target):
    target.removeOverlap()
    target.correctDirection()
    target.round()
    _remove_redundant_points(target)
    target.correctDirection()
    target.canonicalContours()
    target.canonicalStart()
    problems = target.validate(True)
    if problems:
        raise RuntimeError(f"{target.glyphname}: validation flags {problems:#x}")


def _draw_blueprint(target, blueprint):
    for contour in blueprint["ink"]:
        _add_contour(target, contour, clockwise=True)
    for contour in blueprint["cuts"]:
        _add_contour(target, contour, clockwise=False)
    target.width = 500
    _normalize(target)


def _make_font(style, weight, version):
    design = design_for(style)
    font = fontforge.font()
    font.encoding = "UnicodeFull"
    font.ascent = design.ascent
    font.descent = design.descent
    font.hhea_ascent = design.ascent
    font.hhea_ascent_add = False
    font.hhea_descent = -design.descent
    font.hhea_descent_add = False
    font.hhea_linegap = 0
    font.os2_typoascent = design.ascent
    font.os2_typoascent_add = False
    font.os2_typodescent = -design.descent
    font.os2_typodescent_add = False
    font.os2_typolinegap = 0
    font.os2_winascent = design.ascent
    font.os2_winascent_add = False
    font.os2_windescent = design.descent
    font.os2_windescent_add = False
    font.familyname = "Mambo Font Pilot"
    font.fullname = f"Mambo Font Pilot {style}"
    font.fontname = f"MamboFontPilot-{style}"
    font.weight = style
    font.version = version
    font.os2_weight = weight
    font.os2_vendor = "MAMB"
    font.os2_use_typo_metrics = True
    font.os2_panose = (2, 11, PANOSE_WEIGHT[weight], 9, 2, 2, 2, 2, 2, 4)
    font.copyright = "Copyright (c) 2026 ProjectMambo"
    font.appendSFNTName("English (US)", 13, "MIT License")
    font.appendSFNTName("English (US)", 14, "https://github.com/ProjectMambo/MamboFont/blob/main/LICENSE")
    if weight == 700:
        font.macstyle = 1
        font.os2_stylemap = 0x20

    missing = font.createChar(-1, ".notdef")
    _draw_blueprint(
        missing,
        glyph(
            rectangle(design.ink_left, 0, design.ink_right, design.cap_height),
            cuts=(rectangle(
                design.ink_left + design.thickness,
                design.thickness,
                design.ink_right - design.thickness,
                design.cap_height - design.thickness,
            ),),
        ),
    )
    space = font.createChar(0x20, "space")
    space.width = design.advance
    for char, blueprint in sorted(pilot_glyphs(design).items()):
        target = font.createChar(ord(char))
        _draw_blueprint(target, blueprint)

    _validate_font(font, design)
    return font


def _validate_font(font, design):
    actual = {item.unicode for item in font.glyphs() if item.unicode >= 0}
    if actual != PILOT_CODEPOINTS:
        raise RuntimeError(f"pilot cmap mismatch: {sorted(actual ^ PILOT_CODEPOINTS)}")
    for item in font.glyphs():
        is_ours = item.unicode >= 0 or item.glyphname == ".notdef"
        if is_ours and item.width != design.advance:
            raise RuntimeError(f"{item.glyphname}: advance is {item.width}, expected {design.advance}")
        if item.unicode >= 0:
            left, bottom, right, top = item.boundingBox()
            if left < 0 or right > design.advance or bottom < -design.descent or top > design.ascent:
                raise RuntimeError(f"{item.glyphname}: outline outside design bounds {item.boundingBox()}")
        if is_ours and any(not point.on_curve for contour in item.foreground for point in contour):
            raise RuntimeError(f"{item.glyphname}: direct-outline pilot contains a curve point")
    problems = font.validate(True)
    if problems:
        raise RuntimeError(f"font validation flags {problems:#x}")


def _output_name(style, version, file_format):
    return f"MamboFontPilot-{style}_v{version}.{file_format}"


def _generate(font, destination, design):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".mambofont-generate.", dir=destination.parent) as temporary:
        candidate = Path(temporary) / destination.name
        font.generate(str(candidate), flags=GENERATION_FLAGS)
        reopened = fontforge.open(str(candidate))
        try:
            _validate_font(reopened, design)
        finally:
            reopened.close()
        candidate.replace(destination)


def _selected_formats(values):
    return tuple(dict.fromkeys(values or FORMATS))


def compile_fonts(version, out_dir, formats):
    outputs = []
    for style, weight in WEIGHTS:
        design = design_for(style)
        font = _make_font(style, weight, version)
        try:
            for file_format in formats:
                destination = out_dir / _output_name(style, version, file_format)
                _generate(font, destination, design)
                outputs.append(destination)
        finally:
            font.close()
    return outputs


def command_compile(args):
    for output in compile_fonts(args.version, args.out, _selected_formats(args.formats)):
        print(output)


def command_check(args):
    formats = _selected_formats(args.formats)
    with tempfile.TemporaryDirectory(prefix="mambofont-check.") as temporary:
        generated = compile_fonts(args.version, Path(temporary), formats)
        stale = [
            args.out / candidate.name
            for candidate in generated
            if not (args.out / candidate.name).is_file()
            or (args.out / candidate.name).read_bytes() != candidate.read_bytes()
        ]
    if stale:
        for path_value in stale:
            print(f"stale: {path_value}", file=sys.stderr)
        raise SystemExit(1)
    print(f"{len(generated)} pilot files are current")


def _blueprint_card(char, blueprint, design):
    vertical = (0, design.ink_left, design.advance / 2, design.ink_right, design.advance)
    horizontal = (-design.descent, design.descender, 0, design.x_height, design.cap_height, design.ascent)
    guides = "".join(f'<line x1="{x}" y1="{-design.descent}" x2="{x}" y2="{design.ascent}"/>' for x in vertical)
    guides += "".join(f'<line x1="0" y1="{y}" x2="{design.advance}" y2="{y}"/>' for y in horizontal)
    ink = "".join('<polygon points="' + " ".join(f"{x},{y}" for x, y in contour) + '"/>' for contour in blueprint["ink"])
    cuts = "".join('<polygon points="' + " ".join(f"{x},{y}" for x, y in contour) + '"/>' for contour in blueprint["cuts"])
    points = "".join(
        f'<circle cx="{x}" cy="{y}" r="5"/>'
        for contour in (*blueprint["ink"], *blueprint["cuts"])
        for x, y in contour
    )
    return (
        f'<figure><svg viewBox="0 0 {design.advance} {design.upm}" role="img" aria-label="{html.escape(char)} blueprint">'
        f'<g transform="translate(0 {design.ascent}) scale(1 -1)"><g class="guides">{guides}</g>'
        f'<g class="ink">{ink}</g><g class="cuts">{cuts}</g><g class="points">{points}</g></g></svg>'
        f'<figcaption>{html.escape(char)}</figcaption></figure>'
    )


def command_specimen(args):
    font_dir = Path(os.path.relpath(args.fonts.resolve(), args.out.resolve().parent))
    faces = []
    for style, weight in WEIGHTS:
        filename = _output_name(style, args.version, "woff2")
        if not (args.fonts / filename).is_file():
            raise SystemExit(f"missing font: {args.fonts / filename}")
        faces.append(
            f'@font-face {{ font-family:"MamboFontPilot"; src:url("{font_dir / filename}") format("woff2"); font-weight:{weight}; }}'
        )
    samples = "".join(
        f'<section><h2>{style} · {weight}</h2><p class="sample" style="font-weight:{weight}">HOBS ANMVWXZ<br>aegmnr Il 0128<br>Il1 O0 rn m</p>'
        f'<p class="sizes" style="font-weight:{weight}"><span>12px · HOBS ANMVWXZ aegmnr Il 0128</span><span>16px · HOBS ANMVWXZ aegmnr Il 0128</span><span>24px · HOBS ANMVWXZ aegmnr Il 0128</span></p></section>'
        for style, weight in WEIGHTS
    )
    blueprints = "".join(
        f'<section><h2>{style} geometry · {design.thickness} units</h2><div class="blueprints">'
        + "".join(_blueprint_card(char, blueprint, design) for char, blueprint in pilot_glyphs(design).items())
        + "</div></section>"
        for style, design in (("Regular", design_for("Regular")), ("Bold", design_for("Bold")))
    )
    document = f"""<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>MamboFont direct-outline pilot {args.version}</title>
<style>
{''.join(faces)}
:root {{ color-scheme:light dark; font-family:system-ui,sans-serif; }}
body {{ margin:3rem auto; max-width:1200px; padding:0 1.5rem; background:#f4f0e8; color:#181818; }}
section {{ border-top:2px solid; margin-top:2rem; }}
.sample,.sizes {{ font-family:MamboFontPilot,monospace; line-height:1.45; }} .sample {{ font-size:64px; overflow-wrap:anywhere; }}
.sizes {{ display:grid; gap:.6rem; }} .sizes span:nth-child(1) {{ font-size:12px; }} .sizes span:nth-child(2) {{ font-size:16px; }} .sizes span:nth-child(3) {{ font-size:24px; }}
.blueprints {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(90px,1fr)); gap:.75rem; }}
figure {{ margin:0; padding:.5rem; border:1px solid #777; text-align:center; }} svg {{ display:block; width:100%; max-height:220px; }}
.guides {{ fill:none; stroke:#2580d8; stroke-width:2; vector-effect:non-scaling-stroke; opacity:.45; }}
.ink {{ fill:currentColor; }} .cuts {{ fill:#f4f0e8; stroke:#df6c24; stroke-width:2; vector-effect:non-scaling-stroke; }}
.points {{ fill:#e13b35; }} figcaption {{ font-family:monospace; font-weight:700; }}
@media (prefers-color-scheme:dark) {{ body {{ background:#171717; color:#f4f0e8; }} .cuts {{ fill:#171717; }} }}
</style><body><h1>MamboFont direct-outline pilot</h1><p>Incomplete review font: 500-unit cells, straight filled contours, no stroked paths. Red dots are blueprint vertices; blue lines are design guides.</p>{samples}{blueprints}</body></html>
"""
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(document)
    print(args.out)


def _add_build_options(parser):
    parser.add_argument("version", nargs="?", type=validate_version, default=VERSION)
    parser.add_argument("--out", type=Path, default=PROJECT_ROOT / "build" / "pilot")
    parser.add_argument("--format", dest="formats", nargs="+", choices=FORMATS)


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    compile_parser = commands.add_parser("compile", help="generate pilot font files")
    _add_build_options(compile_parser)
    compile_parser.set_defaults(run=command_compile)
    check_parser = commands.add_parser("check", help="rebuild and compare pilot files")
    _add_build_options(check_parser)
    check_parser.set_defaults(run=command_check)
    specimen_parser = commands.add_parser("specimen", help="write the pilot review page")
    specimen_parser.add_argument("version", nargs="?", type=validate_version, default=VERSION)
    specimen_parser.add_argument("--fonts", type=Path, default=PROJECT_ROOT / "build" / "pilot")
    specimen_parser.add_argument("--out", type=Path, default=PROJECT_ROOT / "specimen.html")
    specimen_parser.set_defaults(run=command_specimen)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.run(args)


if __name__ == "__main__":
    main()
