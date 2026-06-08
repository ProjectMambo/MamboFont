#!/usr/bin/env python3
import sys
from pathlib import Path
try:
    import fontforge
except ImportError:
    print("\033[0;31m[!] Error: FontForge Python bindings not found.\033[0m")
    print("    Please run: 'sudo pacman -S fontforge'")
    sys.exit(1)

# Color codes for clean scannable terminal output
GREEN = '\033[0;32m'
RED   = '\033[0;31m'
BLUE  = '\033[0;34m'
NC    = '\033[0m' # No Color

# ----------------------------------------------------------------
# Font family name
# ----------------------------------------------------------------
FAMILY_NAME = "Mambo Font"

# ----------------------------------------------------------------
# Weight folders to compile (relative to drawings/exported/)
# Each entry: (folder_name, style_name, os2_weight)
#
# style_name -> used in fullname and as the TTF suffix
# os2_weight -> numeric weight for OS/2 table (400=Regular, 600=SemiBold)
# ----------------------------------------------------------------
WEIGHTS = [
    ("regular",  "Regular",  400),
    ("bold", "Bold", 700),
]

# ----------------------------------------------------------------
# Subfolders inside each weight folder
# SCAN_SUBDIRS -> width 500, centered  (glyphs/letters/symbols)
# ICON_SUBDIRS -> width 1000, no shift (icons)
# ----------------------------------------------------------------
SCAN_SUBDIRS = [
    "alphabetupper",
    "alphabetlower",
    "number",
    "punctuation",
    "control",
    "symbol",
]

ICON_SUBDIRS = [
    "icons",
]

# ----------------------------------------------------------------
# Named ASCII & Extended ASCII (Latin-1 Supplement) glyphs — 
# maps stem name (case-insensitive) to its Unicode codepoint.
# ----------------------------------------------------------------
ASCII_NAME_MAP = {
    # Whitespace / control
    "space":        0x0020,
    "nbsp":         0x00A0,
    "tab":          0x0009,
    "newline":      0x000A,
    "return":       0x000D,
    "escape":       0x001B,
    "esc":          0x001B,
    "delete":       0x007F,
    "del":          0x007F,
    "backspace":    0x0008,
    "null":         0x0000,
    
    # Punctuation / symbols
    "exclam":       0x0021,
    "exclamation":  0x0021,
    "quotedbl":     0x0022,
    "quote":        0x0022,
    "numbersign":   0x0023,
    "hash":         0x0023,
    "dollar":       0x0024,
    "percent":      0x0025,
    "ampersand":    0x0026,
    "amp":          0x0026,
    "quotesingle":  0x0027,
    "apostrophe":   0x0027,
    "tick":         0x0027,
    "parenleft":    0x0028,
    "parenright":   0x0029,
    "asterisk":     0x002A,
    "star":         0x002A,
    "plus":         0x002B,
    "comma":        0x002C,
    "hyphen":       0x002D,
    "minus":        0x002D,
    "dash":         0x002D,
    "period":       0x002E,
    "dot":          0x002E,
    "fullstop":     0x002E,
    "slash":        0x002F,
    "solidus":      0x002F,
    "colon":        0x003A,
    "semicolon":    0x003B,
    "less":         0x003C,
    "lessthan":     0x003C,
    "equal":        0x003D,
    "equals":       0x003D,
    "greater":      0x003E,
    "greaterthan":  0x003E,
    "question":     0x003F,
    "questionmark": 0x003F,
    "at":           0x0040,
    "atsign":       0x0040,
    "bracketleft":  0x005B,
    "backslash":    0x005C,
    "bracketright": 0x005D,
    "caret":        0x005E,
    "circumflex":   0x005E,
    "underscore":   0x005F,
    "grave":        0x0060,
    "backtick":     0x0060,
    "braceleft":    0x007B,
    "braceright":   0x007D,
    "bar":          0x007C,
    "pipe":         0x007C,
    "verticalbar":  0x007C,
    "tilde":        0x007E,

    # ------------------------------------------------------------
    # Extended ASCII / Latin-1 Supplement (0x0080 - 0x00FF)
    # ------------------------------------------------------------
    # C1 Control Characters (0x0080 - 0x009F) commonly used as symbols
    "euro":           0x20AC, # Often mapped from 0x80 in Windows-1252
    "bullet":         0x2022, # Often mapped from 0x95 in Windows-1252
    "trademark":      0x2122, # Often mapped from 0x99 in Windows-1252
    "tm":             0x2122,

    # Symbols & Punctuation (0x00A1 - 0x00BF)
    "exclamdown":     0x00A1,
    "cent":           0x00A2,
    "sterling":       0x00A3,
    "pound":          0x00A3,
    "currency":       0x00A4,
    "yen":            0x00A5,
    "brokenbar":      0x00A6,
    "section":        0x00A7,
    "dieresis":       0x00A8,
    "umlaut":         0x00A8,
    "copyright":      0x00A9,
    "copy":           0x00A9,
    "ordfeminine":    0x00AA,
    "guillemotleft":  0x00AB,
    "guilsinglleft": 0x00AB,
    "not":            0x00AC,
    "softhyphen":     0x00AD,
    "registered":     0x00AE,
    "reg":            0x00AE,
    "macron":         0x00AF,
    "degree":         0x00B0,
    "deg":            0x00B0,
    "plusminus":      0x00B1,
    "twosuperior":    0x00B2,
    "threesuperior":  0x00B3,
    "acute":          0x00B4,
    "micro":          0x00B5,
    "paragraph":      0x00B6,
    "pilcrow":        0x00B6,
    "periodcentered": 0x00B7,
    "middot":         0x00B7,
    "cedilla":        0x00B8,
    "onesuperior":    0x00B9,
    "ordmasculine":   0x00BA,
    "guillemotright": 0x00BB,
    "guilsinglright":0x00BB,
    "onequarter":     0x00BC,
    "onehalf":        0x00BD,
    "threequarters":  0x00BE,
    "questiondown":   0x00BF,

    # Uppercase Accented Letters (0x00C0 - 0x00D6)
    "agrave":         0x00C0,
    "aacute":         0x00C1,
    "acircumflex":    0x00C2,
    "atilde":         0x00C3,
    "adieresis":      0x00C4,
    "aumlaut":        0x00C4,
    "aring":          0x00C5,
    "ae":             0x00C6,
    "ccedilla":       0x00C7,
    "egrave":         0x00C8,
    "eacute":         0x00C9,
    "ecircumflex":    0x00CA,
    "edieresis":      0x00CB,
    "eumlaut":        0x00CB,
    "igrave":         0x00CC,
    "italic":         0x00CD, # 'italic' alias or 'iacute'
    "iacute":         0x00CD,
    "icircumflex":    0x00CE,
    "idieresis":      0x00CF,
    "iumlaut":        0x00CF,
    "eth":            0x00D0,
    "ntilde":         0x00D1,
    "ograve":         0x00D2,
    "oacute":         0x00D3,
    "ocircumflex":    0x00D4,
    "otilde":         0x00D5,
    "odieresis":      0x00D6,
    "oumlaut":        0x00D6,

    # Mathematical / Special (0x00D7 - 0x00DF)
    "multiply":       0x00D7,
    "times":          0x00D7,
    "oslash":         0x00D8,
    "ugrave":         0x00D9,
    "uacute":         0x00DA,
    "ucircumflex":    0x00DB,
    "udieresis":      0x00DC,
    "uumlaut":        0x00DC,
    "yacute":         0x00DD,
    "thorn":          0x00DE,
    "germandbls":     0x00DF,
    "ss":             0x00DF,

    # Lowercase Accented Letters & Math (0x00E0 - 0x00FF)
    "agrave_lc":      0x00E0,
    "aacute_lc":      0x00E1,
    "acircumflex_lc": 0x00E2,
    "atilde_lc":      0x00E3,
    "adieresis_lc":   0x00E4,
    "aumlaut_lc":     0x00E4,
    "aring_lc":       0x00E5,
    "ae_lc":          0x00E6,
    "ccedilla_lc":    0x00E7,
    "egrave_lc":      0x00E8,
    "eacute_lc":      0x00E9,
    "ecircumflex_lc": 0x00EA,
    "edieresis_lc":   0x00EB,
    "eumlaut_lc":     0x00EB,
    "igrave_lc":      0x00EC,
    "iacute_lc":      0x00ED,
    "icircumflex_lc": 0x00EE,
    "idieresis_lc":   0x00EF,
    "iumlaut_lc":     0x00EF,
    "eth_lc":         0x00F0,
    "ntilde_lc":      0x00F1,
    "ograve_lc":      0x00F2,
    "oacute_lc":      0x00F3,
    "ocircumflex_lc": 0x00F4,
    "otilde_lc":      0x00F5,
    "odieresis_lc":   0x00F6,
    "oumlaut_lc":     0x00F6,
    "divide":         0x00F7,
    "div":            0x00F7,
    "oslash_lc":      0x00F8,
    "ugrave_lc":      0x00F9,
    "uacute_lc":      0x00FA,
    "ucircumflex_lc": 0x00FB,
    "udieresis_lc":   0x00FC,
    "uumlaut_lc":     0x00FC,
    "yacute_lc":      0x00FD,
    "thorn_lc":       0x00FE,
    "ydieresis":      0x00FF,
    "yumlaut":        0x00FF,
}


# ----------------------------------------------------------------
# Glyphs with no visible paths get a proper advance width but
# no outlines. We detect this by checking the SVG file itself —
# if it contains no <path>, <rect>, <circle>, <ellipse>,
# <polygon>, <polyline>, or <use> elements, it's empty.
# ----------------------------------------------------------------
import xml.etree.ElementTree as _ET

_SHAPE_TAGS = {
    "path", "rect", "circle", "ellipse",
    "polygon", "polyline", "line", "use", "g",
}

def has_visible_outlines(svg_path: Path) -> bool:
    """Return True if the SVG contains at least one drawable shape element."""
    try:
        tree = _ET.parse(svg_path)
        root = tree.getroot()
        ns = root.tag.split("}")[0].lstrip("{") if "}" in root.tag else ""
        prefix = f"{{{ns}}}" if ns else ""
        for tag in _SHAPE_TAGS:
            if root.find(f".//{prefix}{tag}") is not None:
                return True
    except Exception:
        pass
    return False


def get_sorted_svg_files(base_path):
    """Recursively scan directory in strict alphabetical order."""
    items = sorted(base_path.iterdir(), key=lambda x: x.name.lower())
    svg_files = []
    for item in items:
        if item.is_dir():
            svg_files.extend(get_sorted_svg_files(item))
        elif item.is_file() and item.suffix.lower() == ".svg":
            svg_files.append(item)
    return svg_files


def resolve_codepoint(stem):
    """
    Priority:
      1. .notdef                      -> special sentinel -1
      2. Single printable ASCII char  -> its ordinal
      3. Known ASCII name (lookup)    -> mapped codepoint
      4. Everything else              -> None (caller assigns PUA)
    """
    if stem == ".notdef":
        return -1, ".notdef  (special)"

    if len(stem) == 1 and 0x20 <= ord(stem) <= 0x7E:
        cp = ord(stem)
        return cp, f"U+{cp:04X}  (ASCII '{stem}')"

    cp = ASCII_NAME_MAP.get(stem.lower())
    if cp is not None:
        return cp, f"U+{cp:04X}  (ASCII name '{stem}')"

    return None, None


def center_glyph(glyph, target_width=500):
    """Center outlines horizontally within target_width."""
    bbox = glyph.boundingBox()
    if bbox is None or bbox == (0, 0, 0, 0):
        glyph.width = target_width
        return
    xmin, _, xmax, _ = bbox
    glyph_w  = xmax - xmin
    offset_x = (target_width - glyph_w) / 2 - xmin
    glyph.transform((1, 0, 0, 1, offset_x, 0))
    glyph.width = target_width


def make_glyph(font, codepoint, stem):
    """
    Create (or reuse) a glyph slot.
    codepoint == -1 means .notdef — FontForge requires createChar(-1, '.notdef').
    Everything else uses the standard uni<XXXX> name.
    """
    if codepoint == -1:
        return font.createChar(-1, ".notdef")
    return font.createChar(codepoint, f"uni{codepoint:04X}")


def build_weight(weight_dir, style_name, os2_weight, version, output_dir, project_root):
    """Compile TTF and WOFF2 files for a single weight folder."""

    # ---- font metadata ----
    font = fontforge.font()
    font.familyname = FAMILY_NAME
    font.fullname   = f"{FAMILY_NAME} {style_name}"
    font.fontname   = f"{FAMILY_NAME.replace(' ', '')}-{style_name}"
    font.version    = version
    font.weight     = style_name

    # OS/2 weight class so apps recognise bold/regular correctly
    font.os2_weight = os2_weight

    # Mark as bold in head flags when weight >= 600
    if os2_weight >= 600:
        font.macstyle  = 0b00000001  # bold bit
        font.os2_stylemap = 0b00100000  # OS/2 bold

    font.ascent  = 800
    font.descent = 200

    safe_style = style_name.replace(" ", "")
    output_ttf   = output_dir / f"MamboFont-{safe_style}_v{version}.ttf"
    output_woff2 = output_dir / f"MamboFont-{safe_style}_v{version}.woff2"

    print(f"\n{BLUE}=========================================={NC}")
    print(f" Weight:  {GREEN}{style_name}{NC}  (OS/2 {os2_weight})")
    print(f" Source:  {weight_dir.relative_to(project_root)}")
    print(f" Outputs: {output_ttf.relative_to(project_root)}")
    print(f"          {output_woff2.relative_to(project_root)}")
    print(f"{BLUE}=========================================={NC}")

    pua_counter = 0xE000

    # ---- SCAN subdirs (centered, width 500) ----
    for sub in SCAN_SUBDIRS:
        scan_dir = weight_dir / sub
        if not scan_dir.exists():
            print(f"\n{RED}[!] Not found, skipping:{NC} {sub}")
            continue

        svg_files = get_sorted_svg_files(scan_dir)
        if not svg_files:
            print(f"\n   -> No SVGs in {sub}, skipping.")
            continue

        print(f"\n{BLUE}[*] Scan:{NC} {sub}  ({len(svg_files)} glyphs)")

        for file in svg_files:
            stem = file.stem
            codepoint, slot_label = resolve_codepoint(stem)

            if codepoint is None:
                codepoint   = pua_counter
                slot_label  = f"U+{codepoint:04X}  (PUA)"
                pua_counter += 1

            glyph = make_glyph(font, codepoint, stem)
            if has_visible_outlines(file):
                glyph.importOutlines(str(file.resolve()))
                center_glyph(glyph)
            else:
                glyph.width = 500  # blank glyph, just advance width
            print(f"   -> {slot_label}  {GREEN}{stem}{NC}")

    # ---- ICON subdirs (width 1000, no centering) ----
    for sub in ICON_SUBDIRS:
        icon_dir = weight_dir / sub
        if not icon_dir.exists():
            print(f"\n{RED}[!] Not found, skipping:{NC} {sub}")
            continue

        svg_files = get_sorted_svg_files(icon_dir)
        if not svg_files:
            print(f"\n   -> No SVGs in {sub}, skipping.")
            continue

        print(f"\n{BLUE}[*] Icons:{NC} {sub}  ({len(svg_files)} glyphs)")

        for file in svg_files:
            stem = file.stem
            codepoint, slot_label = resolve_codepoint(stem)

            if codepoint is None:
                codepoint   = pua_counter
                slot_label  = f"U+{codepoint:04X}  (PUA)"
                pua_counter += 1

            glyph = make_glyph(font, codepoint, stem)
            if has_visible_outlines(file):
                glyph.importOutlines(str(file.resolve()))
            glyph.width = 1000
            print(f"   -> {slot_label}  {GREEN}{stem}{NC}")

    pua_used = pua_counter - 0xE000
    if pua_used:
        print(f"\n{BLUE}[i] PUA slots used:{NC} {pua_used}  (U+E000 – U+{pua_counter - 1:04X})")

    # Generate TTF copy
    font.generate(str(output_ttf))
    print(f"\n{GREEN}[+] Generated TTF:{NC} {output_ttf.name}")
    
    # Generate WOFF2 copy
    font.generate(str(output_woff2))
    print(f"{GREEN}[+] Generated WOFF2:{NC} {output_woff2.name}")


def main():
    if len(sys.argv) < 2:
        print(f"{RED}Usage: {sys.argv[0]} <version>{NC}")
        sys.exit(1)

    version = sys.argv[1]

    script_dir   = Path(__file__).resolve().parent
    project_root = script_dir.parent
    exported_dir = project_root / "drawings" / "exported"
    output_dir   = project_root / "ttf"
    output_dir.mkdir(exist_ok=True)

    print(f"{BLUE}------------------------------------------{NC}")
    print(f" Family:  {GREEN}{FAMILY_NAME}{NC}")
    print(f" Version: {GREEN}{version}{NC}")
    print(f" Weights: {GREEN}{', '.join(w[1] for w in WEIGHTS)}{NC}")
    print(f"{BLUE}------------------------------------------{NC}")

    for folder_name, style_name, os2_weight in WEIGHTS:
        weight_dir = exported_dir / folder_name
        if not weight_dir.exists():
            print(f"\n{RED}[!] Weight folder not found, skipping:{NC} {folder_name}")
            continue
        build_weight(weight_dir, style_name, os2_weight, version, output_dir, project_root)

    print(f"\n{BLUE}------------------------------------------{NC}")
    print(f"{GREEN}[+] All weights compiled successfully (TTF & WOFF2)!{NC}")
    print(f"{BLUE}------------------------------------------{NC}")

if __name__ == "__main__":
    main()