#!/usr/bin/env python3
"""Build and verify Mambo Font directly from Python rules."""

import argparse
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

from sources import text
from sources.geometry import glyph, loop, path


VERSION = "0.3.0"
WEIGHTS = (("Regular", 400, 80), ("Medium", 500, 93), ("SemiBold", 600, 107), ("Bold", 700, 120))
FORMATS = ("ttf", "woff2")
GENERATION_FLAGS = ("opentype", "no-FFTM-table")
PANOSE_WEIGHT = {400: 5, 500: 6, 600: 7, 700: 8}


def validate_version(value):
    if not re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", value):
        raise argparse.ArgumentTypeError("version must be X.Y.Z")
    return value


def component_name(source_name):
    return "component_" + source_name.lstrip(".").replace(".", "_")


def draw_spec(target, spec, stroke):
    paths = spec.get("paths", ())
    if paths:
        pen = target.glyphPen(replace=False)
        for points in paths:
            closed = len(points) > 2 and points[0] == points[-1]
            pen.moveTo(points[0])
            for point_value in points[1:-1] if closed else points[1:]:
                pen.lineTo(point_value)
            pen.closePath() if closed else pen.endPath()
        del pen
        target.stroke(
            "circular",
            stroke,
            cap="butt",
            join="miter",
            joinlimit=2.0,
            removeoverlap="layer",
            simplify=True,
            accuracy=0.25,
            extrema=True,
        )

    polygons = list(spec.get("fills", ()))
    for x, y, scale in spec.get("dots", ()):
        half = round(stroke * scale / 2)
        polygons.append(((x - half, y - half), (x - half, y + half), (x + half, y + half), (x + half, y - half)))

    if polygons:
        pen = target.glyphPen(replace=False)
        for points in polygons:
            pen.moveTo(points[0])
            for point_value in points[1:]:
                pen.lineTo(point_value)
            pen.closePath()
        del pen

    clean_glyph(target)


def clean_glyph(target):
    for _ in range(3):
        target.correctDirection()
        target.removeOverlap()
        target.correctDirection()
        target.simplify(0.1, ("mergelines", "setstarttoextremum"))
        target.addExtrema("all")
        target.round()
        if target.validate(True) == 0:
            break


def flatten_references(target):
    if target.references:
        target.unlinkRef()
    clean_glyph(target)


def make_font(family, style, weight):
    font = fontforge.font()
    font.encoding = "UnicodeFull"
    font.ascent = 800
    font.descent = 200
    font.hhea_ascent = 900
    font.hhea_ascent_add = False
    font.hhea_descent = -200
    font.hhea_descent_add = False
    font.hhea_linegap = 0
    font.os2_typoascent = 800
    font.os2_typoascent_add = False
    font.os2_typodescent = -200
    font.os2_typodescent_add = False
    font.os2_typolinegap = 0
    font.os2_winascent = 900
    font.os2_winascent_add = False
    font.os2_windescent = 200
    font.os2_windescent_add = False
    font.familyname = family
    font.fullname = f"{family} {style}"
    font.fontname = f"{family.replace(' ', '')}-{style}"
    font.weight = style
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
    return font


def make_notdef(font, advance, stroke):
    inset = round(advance * 0.15)
    target = font.createChar(-1, ".notdef")
    draw_spec(
        target,
        glyph(loop((inset, 0), (advance - inset, 0), (advance - inset, 640), (inset, 640)), path((inset, 0), (advance - inset, 640))),
        stroke,
    )
    target.width = advance


def glyph_name(font, name):
    return component_name(name) if name.startswith(".") else font[ord(name)].glyphname


def accent_offset(base, mark, stroke):
    if mark == ".cedilla":
        return -round(stroke / 2)
    base_top = text.CAP if base == base.upper() and not base.startswith(".") else text.XH
    return round(base_top + stroke / 2 + round(stroke * 0.5) / 2 + 30)


def build_text(style, weight, stroke, version):
    font = make_font("Mambo Font", style, weight)
    font.version = version
    make_notdef(font, 500, stroke)

    for name, spec in sorted(text.COMPONENTS.items()):
        target = font.createChar(-1, component_name(name))
        draw_spec(target, spec, stroke if name == ".dotlessi" else round(stroke * 0.50))
        target.width = 500

    target_set = set(text.TARGET_CODEPOINTS)
    for char, spec in sorted(text.GLYPHS.items(), key=lambda item: ord(item[0])):
        if ord(char) not in target_set:
            continue
        target = font.createChar(ord(char))
        draw_spec(target, spec, stroke)
        target.width = 500

    for char, references in sorted(text.REFERENCES.items(), key=lambda item: ord(item[0])):
        target = font.createChar(ord(char))
        for source_name, matrix in references:
            target.addReference(glyph_name(font, source_name), matrix)
        flatten_references(target)
        target.width = 500

    for codepoint in text.TARGET_CODEPOINTS:
        char = chr(codepoint)
        if char in text.GLYPHS or char in text.REFERENCES:
            continue
        base, mark = text.decomposition(char)
        target = font.createChar(codepoint)
        target.addReference(glyph_name(font, base))
        mark_y = accent_offset(base, mark, stroke)
        target.addReference(component_name(mark), (1, 0, 0, 1, 0, mark_y))
        flatten_references(target)
        target.width = 500

    validate_source(font, set(text.TARGET_CODEPOINTS), 500)
    return font


def validate_source(font, expected_codepoints, advance):
    actual = {item.unicode for item in font.glyphs() if item.unicode >= 0}
    if actual != expected_codepoints:
        missing = sorted(expected_codepoints - actual)
        extra = sorted(actual - expected_codepoints)
        raise RuntimeError(f"cmap mismatch; missing={missing}, extra={extra}")
    wrong_widths = [item.glyphname for item in font.glyphs() if item.width != advance]
    if wrong_widths:
        raise RuntimeError(f"non-{advance}-unit glyphs: {wrong_widths}")
    overhangs = {
        item.glyphname: item.boundingBox()
        for item in font.glyphs()
        if item.unicode >= 0 and (item.boundingBox()[0] < 0 or item.boundingBox()[2] > advance)
    }
    if overhangs:
        raise RuntimeError(f"horizontal cell overhangs: {overhangs}")
    invalid = {item.glyphname: item.validate(True) for item in font.glyphs() if item.validate(True)}
    if invalid:
        raise RuntimeError(f"invalid source outlines: {invalid}")


def output_name(family, style, version, file_format):
    return f"{family}-{style}_v{version}.{file_format}"


def generate(font, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".mambofont-generate.", dir=destination.parent) as temporary:
        candidate = Path(temporary) / destination.name
        font.generate(str(candidate), flags=GENERATION_FLAGS)
        reopened = fontforge.open(str(candidate))
        try:
            invalid = reopened.validate(True)
        finally:
            reopened.close()
        if invalid:
            raise RuntimeError(f"generated font failed validation ({invalid}): {destination.name}")
        candidate.replace(destination)


def selected_formats(values):
    return tuple(dict.fromkeys(values or FORMATS))


def compile_fonts(version, out_dir, formats):
    outputs = []
    for style, weight, stroke in WEIGHTS:
        font = build_text(style, weight, stroke, version)
        try:
            for file_format in formats:
                destination = out_dir / output_name("MamboFont", style, version, file_format)
                generate(font, destination)
                outputs.append(destination)
        finally:
            font.close()
    return outputs


def command_compile(args):
    outputs = compile_fonts(args.version, args.out, selected_formats(args.formats))
    for output in outputs:
        print(output)


def command_check(args):
    formats = selected_formats(args.formats)
    with tempfile.TemporaryDirectory(prefix="mambofont-check.") as temporary:
        generated = compile_fonts(args.version, Path(temporary), formats)
        stale = []
        for candidate in generated:
            expected = args.out / candidate.name
            if not expected.is_file() or expected.read_bytes() != candidate.read_bytes():
                stale.append(expected)
    if stale:
        for path_value in stale:
            print(f"stale: {path_value}", file=sys.stderr)
        raise SystemExit(1)
    print(f"{len(generated)} generated files are current")


def command_specimen(args):
    font_dir = Path(os.path.relpath(args.fonts.resolve(), args.out.resolve().parent))
    faces = []
    for style, weight, _ in WEIGHTS:
        filename = output_name("MamboFont", style, args.version, "woff2")
        if not (args.fonts / filename).is_file():
            raise SystemExit(f"missing font: {args.fonts / filename}")
        faces.append(
            f'@font-face {{ font-family: "MamboFont"; src: url("{font_dir / filename}") format("woff2"); font-weight: {weight}; }}'
        )
    samples = "".join(
        f'<section><h2>{style} · {weight}</h2><p class="sample" style="font-weight:{weight}">MamboFont 0123456789<br>ABCDEFGHIJKLMNOPQRSTUVWXYZ<br>abcdefghijklmnopqrstuvwxyz<br>!&quot;#$%&amp;\'()*+,-./:;&lt;=&gt;?@[\\]^_`{{|}}~<br>ÀÁÂÃÄÅ Æ Ç ÈÉÊË ÌÍÎÏ Ð Ñ ÒÓÔÕÖ Ø ÙÚÛÜ Ý Þ ß<br>àáâãäå æ ç èéêë ìíîï ð ñ òóôõö ø ùúûü ý þ ÿ<br>€ ‚ ƒ „ … † ‡ ˆ ‰ Š ‹ Œ Ž ‘ ’ “ ” • – — ˜ ™ š › œ ž Ÿ</p></section>'
        for style, weight, _ in WEIGHTS
    )
    document = f"""<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Mambo Font {args.version} specimen</title>
<style>
{''.join(faces)}
:root {{ color-scheme: light dark; font-family: system-ui, sans-serif; }}
body {{ margin: 3rem auto; max-width: 1100px; padding: 0 1.5rem; background:#f4f0e8; color:#181818; }}
h1,h2 {{ font-family: MamboFont, monospace; }} section {{ border-top:2px solid; margin-top:2rem; }}
.sample {{ font-family:MamboFont,monospace; font-size:clamp(18px,2.5vw,32px); line-height:1.55; overflow-wrap:anywhere; }}
@media (prefers-color-scheme:dark) {{ body {{ background:#171717; color:#f4f0e8; }} }}
</style><body><h1>Mambo Font {args.version}</h1>{samples}</body></html>
"""
    args.out.write_text(document)
    print(args.out)


def add_build_options(parser):
    parser.add_argument("version", nargs="?", type=validate_version, default=VERSION)
    parser.add_argument("--out", type=Path, default=PROJECT_ROOT / "dist")
    parser.add_argument("--format", dest="formats", nargs="+", choices=FORMATS)


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    compile_parser = commands.add_parser("compile", help="generate font files")
    add_build_options(compile_parser)
    compile_parser.set_defaults(run=command_compile)
    check_parser = commands.add_parser("check", help="rebuild and compare generated files")
    add_build_options(check_parser)
    check_parser.set_defaults(run=command_check)
    specimen_parser = commands.add_parser("specimen", help="write a browser review page")
    specimen_parser.add_argument("version", nargs="?", type=validate_version, default=VERSION)
    specimen_parser.add_argument("--fonts", type=Path, default=PROJECT_ROOT / "dist")
    specimen_parser.add_argument("--out", type=Path, default=PROJECT_ROOT / "specimen.html")
    specimen_parser.set_defaults(run=command_specimen)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.run(args)


if __name__ == "__main__":
    main()
