#!/usr/bin/env python3
"""
mambo_font.py — export SVG layers and/or compile font weights.

Modes:
  export   Export processed SVGs to disk (stroke→path, simplified, written all at once)
  compile  Export in-memory only, then compile TTF + WOFF2 without touching disk SVGs

Usage:
  python mambo_font.py export [layer_filter ...]
  python mambo_font.py compile <version> [layer_filter ...]
"""

import argparse
import io
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

# ── optional fontforge (only needed for compile) ───────────────────────────
try:
    import fontforge as _ff
except ImportError:
    _ff = None

# ── colour codes ───────────────────────────────────────────────────────────
GREEN  = '\033[0;32m'
RED    = '\033[0;31m'
BLUE   = '\033[0;34m'
YELLOW = '\033[0;33m'
NC     = '\033[0m'

# ── project layout ──────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
SVG_DIR      = PROJECT_ROOT / "drawings"
SOURCE       = SVG_DIR / "drawing.svg"
DEST_DIR     = SVG_DIR / "exported"
TTF_DIR      = PROJECT_ROOT / "ttf"

# ── font config ─────────────────────────────────────────────────────────────
FAMILY_NAME = "Mambo Font"

WEIGHTS = [
    ("regular", "Regular", 400),
    ("bold",    "Bold",    700),
]

SCAN_SUBDIRS = ["alphabetupper", "alphabetlower", "number", "punctuation", "control", "symbol"]

# Full-width subdirs (advance width 1000, no horizontal centering).
# Two kinds of entries are allowed:
#   FULLWIDTH_PUA   — glyphs always assigned PUA codepoints (icons, ligatures, etc.)
#   FULLWIDTH_MAPPED — glyphs mapped to their real Unicode codepoints (CJK, symbols, etc.)
# Stem naming rules for FULLWIDTH_MAPPED:
#   • A single CJK (or any non-ASCII) character  e.g. "你"  → ord() of that char
#   • A hex string like "U+4F60" or "4F60"        → parsed codepoint
FULLWIDTH_PUA    = ["icons"]
FULLWIDTH_MAPPED = ["chinese", "unicode"]

SKIP_LAYERS = {"Base"}

# ── ASCII codepoint map ──────────────────────────────────────────────────────
ASCII_NAME_MAP = {
    # ── Whitespace / control ───────────────────────────────────────────────
    "space": 0x0020,
    "nbsp": 0x00A0,
    "tab": 0x0009,
    "newline": 0x000A,
    "return": 0x000D,
    "escape": 0x001B,  "esc": 0x001B,
    "delete": 0x007F,  "del": 0x007F,
    "backspace": 0x0008,
    "null": 0x0000,

    # ── Basic punctuation & symbols (U+0021–U+007E) ────────────────────────
    "exclam": 0x0021,      "exclamation": 0x0021,
    "quotedbl": 0x0022,    "quote": 0x0022,
    "numbersign": 0x0023,  "hash": 0x0023,
    "dollar": 0x0024,
    "percent": 0x0025,
    "ampersand": 0x0026,   "amp": 0x0026,
    "quotesingle": 0x0027, "apostrophe": 0x0027,  "tick": 0x0027,
    "parenleft": 0x0028,
    "parenright": 0x0029,
    "asterisk": 0x002A,    "star": 0x002A,
    "plus": 0x002B,
    "comma": 0x002C,
    "hyphen": 0x002D,      "minus": 0x002D,       "dash": 0x002D,
    "period": 0x002E,      "dot": 0x002E,         "fullstop": 0x002E,
    "slash": 0x002F,       "solidus": 0x002F,
    "colon": 0x003A,
    "semicolon": 0x003B,
    "less": 0x003C,        "lessthan": 0x003C,
    "equal": 0x003D,       "equals": 0x003D,
    "greater": 0x003E,     "greaterthan": 0x003E,
    "question": 0x003F,    "questionmark": 0x003F,
    "at": 0x0040,          "atsign": 0x0040,
    "bracketleft": 0x005B,
    "backslash": 0x005C,
    "bracketright": 0x005D,
    "caret": 0x005E,       "circumflex": 0x005E,
    "underscore": 0x005F,
    "grave": 0x0060,       "backtick": 0x0060,
    "braceleft": 0x007B,
    "bar": 0x007C,         "pipe": 0x007C,        "verticalbar": 0x007C,
    "braceright": 0x007D,
    "tilde": 0x007E,

    # ── Common symbols (non-Latin-1 codepoints) ────────────────────────────
    "euro": 0x20AC,
    "bullet": 0x2022,
    "trademark": 0x2122,   "tm": 0x2122,

    # ── Latin-1 Supplement — symbols (U+00A1–U+00BF) ──────────────────────
    "exclamdown": 0x00A1,
    "cent": 0x00A2,
    "sterling": 0x00A3,    "pound": 0x00A3,
    "currency": 0x00A4,
    "yen": 0x00A5,
    "brokenbar": 0x00A6,
    "section": 0x00A7,
    "dieresis": 0x00A8,    "umlaut": 0x00A8,
    "copyright": 0x00A9,   "copy": 0x00A9,
    "ordfeminine": 0x00AA,
    "guillemotleft": 0x00AB,  "guilsinglleft": 0x00AB,
    "not": 0x00AC,
    "softhyphen": 0x00AD,
    "registered": 0x00AE,  "reg": 0x00AE,
    "macron": 0x00AF,
    "degree": 0x00B0,      "deg": 0x00B0,
    "plusminus": 0x00B1,
    "twosuperior": 0x00B2,
    "threesuperior": 0x00B3,
    "acute": 0x00B4,
    "micro": 0x00B5,
    "paragraph": 0x00B6,   "pilcrow": 0x00B6,
    "periodcentered": 0x00B7,  "middot": 0x00B7,
    "cedilla": 0x00B8,
    "onesuperior": 0x00B9,
    "ordmasculine": 0x00BA,
    "guillemotright": 0x00BB, "guilsinglright": 0x00BB,
    "onequarter": 0x00BC,
    "onehalf": 0x00BD,
    "threequarters": 0x00BE,
    "questiondown": 0x00BF,

    # ── Latin-1 Supplement — uppercase accented (U+00C0–U+00D6) ───────────
    "agrave": 0x00C0,
    "aacute": 0x00C1,
    "acircumflex": 0x00C2,
    "atilde": 0x00C3,
    "adieresis": 0x00C4,   "aumlaut": 0x00C4,
    "aring": 0x00C5,
    "ae": 0x00C6,
    "ccedilla": 0x00C7,
    "egrave": 0x00C8,
    "eacute": 0x00C9,
    "ecircumflex": 0x00CA,
    "edieresis": 0x00CB,   "eumlaut": 0x00CB,
    "igrave": 0x00CC,
    "iacute": 0x00CD,      "italic": 0x00CD,
    "icircumflex": 0x00CE,
    "idieresis": 0x00CF,   "iumlaut": 0x00CF,
    "eth": 0x00D0,
    "ntilde": 0x00D1,
    "ograve": 0x00D2,
    "oacute": 0x00D3,
    "ocircumflex": 0x00D4,
    "otilde": 0x00D5,
    "odieresis": 0x00D6,   "oumlaut": 0x00D6,

    # ── Latin-1 Supplement — math & misc (U+00D7–U+00DF) ─────────────────
    "multiply": 0x00D7,    "times": 0x00D7,
    "oslash": 0x00D8,
    "ugrave": 0x00D9,
    "uacute": 0x00DA,
    "ucircumflex": 0x00DB,
    "udieresis": 0x00DC,   "uumlaut": 0x00DC,
    "yacute": 0x00DD,
    "thorn": 0x00DE,
    "germandbls": 0x00DF,  "ss": 0x00DF,

    # ── Latin-1 Supplement — lowercase accented (U+00E0–U+00FF) ──────────
    "agrave_lc": 0x00E0,
    "aacute_lc": 0x00E1,
    "acircumflex_lc": 0x00E2,
    "atilde_lc": 0x00E3,
    "adieresis_lc": 0x00E4,   "aumlaut_lc": 0x00E4,
    "aring_lc": 0x00E5,
    "ae_lc": 0x00E6,
    "ccedilla_lc": 0x00E7,
    "egrave_lc": 0x00E8,
    "eacute_lc": 0x00E9,
    "ecircumflex_lc": 0x00EA,
    "edieresis_lc": 0x00EB,   "eumlaut_lc": 0x00EB,
    "igrave_lc": 0x00EC,
    "iacute_lc": 0x00ED,
    "icircumflex_lc": 0x00EE,
    "idieresis_lc": 0x00EF,   "iumlaut_lc": 0x00EF,
    "eth_lc": 0x00F0,
    "ntilde_lc": 0x00F1,
    "ograve_lc": 0x00F2,
    "oacute_lc": 0x00F3,
    "ocircumflex_lc": 0x00F4,
    "otilde_lc": 0x00F5,
    "odieresis_lc": 0x00F6,   "oumlaut_lc": 0x00F6,
    "divide": 0x00F7,          "div": 0x00F7,
    "oslash_lc": 0x00F8,
    "ugrave_lc": 0x00F9,
    "uacute_lc": 0x00FA,
    "ucircumflex_lc": 0x00FB,
    "udieresis_lc": 0x00FC,   "uumlaut_lc": 0x00FC,
    "yacute_lc": 0x00FD,
    "thorn_lc": 0x00FE,
    "ydieresis": 0x00FF,       "yumlaut": 0x00FF,
}

# ── Unicode name map — common non-ASCII named glyphs ───────────────────────
# Covers arrows, math operators, geometric shapes, box-drawing, dingbats,
# miscellaneous symbols, and CJK/Japanese/Korean basics.
# Stem names are case-insensitive. Add more as needed.
UNICODE_NAME_MAP = {
    # ── Arrows (U+2190–U+21FF) ─────────────────────────────────────────────
    "arrowleft":               0x2190,
    "arrowup":                 0x2191,
    "arrowright":              0x2192,
    "arrowdown":               0x2193,
    "arrowleftright":          0x2194,
    "arrowupdown":             0x2195,
    "arrownwse":               0x2196,
    "arrownesw":               0x2197,
    "arrowsene":               0x2198,
    "arrowswne":               0x2199,
    "arrowdoubleleft":         0x21D0,
    "arrowdoubleup":           0x21D1,
    "arrowdoubleright":        0x21D2,
    "arrowdoubledown":         0x21D3,
    "arrowdoubleleftright":    0x21D4,
    "arrowdoubleupdown":       0x21D5,
    "arrowlefthook":           0x21A9,  # ↩
    "arrowrighthook":          0x21AA,  # ↪
    "arrowcircleleft":         0x21BA,
    "arrowcircleright":        0x21BB,
    "arrowtripleright":        0x21D2,
    "arrowlongright":          0x27F6,
    "arrowlongleft":           0x27F5,
    "arrowlongleftright":      0x27F7,

    # ── Mathematical operators (U+2200–U+22FF) ─────────────────────────────
    "forall":                  0x2200,
    "complement":              0x2201,
    "partial":                 0x2202,
    "thereexists":             0x2203,
    "emptyset":                0x2205,
    "nabla":                   0x2207,
    "element":                 0x2208,
    "notelement":              0x2209,
    "suchthat":                0x220B,
    "product":                 0x220F,
    "coproduct":               0x2210,
    "sum":                     0x2211,
    "minus":                   0x2212,
    "minusplus":               0x2213,
    "dotplus":                 0x2214,
    "divslash":                0x2215,
    "asteriskop":              0x2217,
    "ring":                    0x2218,
    "bulletop":                0x2219,
    "sqrt":                    0x221A,
    "infinity":                0x221E,
    "angle":                   0x2220,
    "rightangle":              0x221F,
    "and":                     0x2227,
    "or":                      0x2228,
    "intersection":            0x2229,
    "union":                   0x222A,
    "integral":                0x222B,
    "doubleintegral":          0x222C,
    "tripleintegral":          0x222D,
    "therefore":               0x2234,
    "because":                 0x2235,
    "similar":                 0x223C,
    "approx":                  0x2248,
    "notequal":                0x2260,
    "identical":               0x2261,
    "lessequal":               0x2264,
    "greaterequal":            0x2265,
    "muchless":                0x226A,
    "muchgreater":             0x226B,
    "subset":                  0x2282,
    "superset":                0x2283,
    "notsubset":               0x2284,
    "subsetequal":             0x2286,
    "supersetequal":           0x2287,
    "circleplus":              0x2295,
    "circleminus":             0x2296,
    "circletimes":             0x2297,
    "circlediv":               0x2298,
    "circledot":               0x2299,
    "perpendicular":           0x22A5,
    "dots":                    0x22EF,  # ⋯
    "vdots":                   0x22EE,  # ⋮
    "ddots":                   0x22F1,  # ⋱

    # ── Miscellaneous technical (U+2300–U+23FF) ────────────────────────────
    "diameter":                0x2300,
    "house":                   0x2302,
    "caretinsert":             0x2303,
    "keyboard":                0x2328,
    "erase":                   0x2326,
    "return2":                 0x23CE,
    "shift":                   0x21E7,
    "capslock":                0x21EA,
    "option":                  0x2325,
    "command":                 0x2318,
    "enter":                   0x2386,
    "delete2":                 0x2326,
    "escape2":                 0x238B,
    "hourglassempty":          0x29D6,
    "hourglass":               0x231B,
    "watch":                   0x231A,
    "alarm":                   0x23F0,
    "stopwatch":               0x23F1,
    "timer":                   0x23F2,

    # ── Letterlike symbols (U+2100–U+214F) ────────────────────────────────
    "account":                 0x2100,
    "addressbook":             0x2101,
    "celsius":                 0x2103,
    "fahrenheit":              0x2109,
    "script":                  0x210E,
    "numero":                  0x2116,
    "ohm":                     0x2126,
    "angstrom":                0x212B,
    "estimated":               0x212E,
    "onethird":                0x2153,
    "twothirds":               0x2154,
    "onefifth":                0x2155,
    "oneeighth":               0x215B,
    "threeeighths":            0x215C,
    "fiveeighths":             0x215D,
    "seveneighths":            0x215E,

    # ── Geometric shapes (U+25A0–U+25FF) ──────────────────────────────────
    "squarefilled":            0x25A0,
    "squareempty":             0x25A1,
    "squaresmall":             0x25AA,
    "rectfilled":              0x25AC,
    "triangleupfilled":        0x25B2,
    "triangleup":              0x25B3,
    "trianglerightfilled":     0x25B6,
    "triangleright":           0x25B7,
    "triangledownfilled":      0x25BC,
    "triangledown":            0x25BD,
    "triangleleftfilled":      0x25C0,
    "triangleleft":            0x25C1,
    "diamondfilled":           0x25C6,
    "diamond":                 0x25C7,
    "lozenge":                 0x25CA,
    "circle":                  0x25CB,
    "circlefilled":            0x25CF,
    "circlesmall":             0x25E6,
    "bullseye":                0x25CE,
    "fisheye":                 0x25C9,
    "pentagon":                0x2B1F,
    "hexagon":                 0x2B22,
    "octagon":                 0x2BC0,
    "star4":                   0x2726,
    "star5":                   0x2605,
    "star5empty":              0x2606,
    "star6":                   0x2736,
    "star8":                   0x2734,
    "star12":                  0x2733,

    # ── Box drawing (U+2500–U+257F) ────────────────────────────────────────
    "boxhorizontal":           0x2500,
    "boxvertical":             0x2502,
    "boxcornertl":             0x250C,
    "boxcornertr":             0x2510,
    "boxcornerbl":             0x2514,
    "boxcornerbr":             0x2518,
    "boxcrossleft":            0x251C,
    "boxcrossright":           0x2524,
    "boxcrosstop":             0x252C,
    "boxcrossbottom":          0x2534,
    "boxcross":                0x253C,
    "boxdoublehorizontal":     0x2550,
    "boxdoublevertical":       0x2551,

    # ── Dingbats & symbols (U+2700–U+27BF) ────────────────────────────────
    "scissors":                0x2702,
    "check":                   0x2713,
    "checkbold":               0x2714,
    "cross":                   0x2715,
    "crossbold":               0x2716,
    "crossoutline":            0x2717,
    "asterisk4":               0x2722,
    "asterisk5":               0x2723,
    "asterisk6":               0x2725,
    "asterisk8":               0x2731,
    "snowflake":               0x2744,
    "sparkle":                 0x2747,
    "arrowrightfilled":        0x279C,
    "arrowrightopen":          0x279B,

    # ── Miscellaneous symbols (U+2600–U+26FF) ─────────────────────────────
    "sun":                     0x2600,
    "suncloud":                0x26C5,
    "cloud":                   0x2601,
    "umbrella":                0x2602,
    "snowman":                 0x2603,
    "comet":                   0x2604,
    "moon":                    0x263D,
    "moonstar":                0x2604,
    "earth":                   0x2641,
    "phone":                   0x260E,
    "phonehandset":            0x2121,
    "envelope":                0x2709,
    "pencil":                  0x270F,
    "pencilright":             0x2710,
    "nib":                     0x2711,
    "nibfilled":               0x2712,
    "magnify":                 0x2315,
    "flag":                    0x2691,
    "flagfilled":              0x2690,
    "anchor":                  0x2693,
    "warning":                 0x26A0,
    "warningfilled":           0x26A1,
    "noentry":                 0x26D4,
    "recycle":                 0x267B,
    "peace":                   0x262E,
    "yinyang":                 0x262F,
    "heart":                   0x2665,
    "heartoutline":            0x2661,
    "club":                    0x2663,
    "cluboutline":             0x2667,
    "spade":                   0x2660,
    "spadeoutline":            0x2664,
    "musicnote":               0x266A,
    "musicnotes":              0x266B,
    "sharp":                   0x266F,
    "flat":                    0x266D,

    # ── Enclosed alphanumerics (U+2460–U+24FF) ─────────────────────────────
    "circled1":                0x2460,
    "circled2":                0x2461,
    "circled3":                0x2462,
    "circled4":                0x2463,
    "circled5":                0x2464,
    "circled6":                0x2465,
    "circled7":                0x2466,
    "circled8":                0x2467,
    "circled9":                0x2468,
    "circled10":               0x2469,
    "circledA":                0x24B6,
    "circledB":                0x24B7,
    "circledC":                0x24B8,

    # ── Supplemental arrows & math (U+27F0–U+27FF, U+2900–U+297F) ──────────
    "arrowleftdoublelong":     0x27F8,
    "arrowrightdoublelong":    0x27F9,
    "arrowleftrightdoublelong":0x27FA,
    "arrowrightlong2":         0x27A1,
    "arrowleftlong2":          0x2B05,
    "arrowuplong":             0x2B06,
    "arrowdownlong":           0x2B07,
    "arrowupleftlong":         0x2B09,
    "arrowuprightlong":        0x2B08,

    # ── Superscript / subscript (U+2070–U+209F) ────────────────────────────
    "sup0":                    0x2070,
    "sup1":                    0x00B9,
    "sup2":                    0x00B2,
    "sup3":                    0x00B3,
    "sup4":                    0x2074,
    "sup5":                    0x2075,
    "sup6":                    0x2076,
    "sup7":                    0x2077,
    "sup8":                    0x2078,
    "sup9":                    0x2079,
    "supplus":                 0x207A,
    "supminus":                0x207B,
    "supequal":                0x207C,
    "supn":                    0x207F,
    "sub0":                    0x2080,
    "sub1":                    0x2081,
    "sub2":                    0x2082,
    "sub3":                    0x2083,
    "sub4":                    0x2084,
    "sub5":                    0x2085,
    "sub6":                    0x2086,
    "sub7":                    0x2087,
    "sub8":                    0x2088,
    "sub9":                    0x2089,

    # ── General punctuation (U+2000–U+206F) ────────────────────────────────
    "enquad":                  0x2000,
    "emquad":                  0x2001,
    "enspace":                 0x2002,
    "emspace":                 0x2003,
    "thickspace":              0x2004,
    "medspace":                0x2005,
    "thinspace":               0x2009,
    "hairspace":               0x200A,
    "zwnj":                    0x200C,
    "zwj":                     0x200D,
    "lrm":                     0x200E,
    "rlm":                     0x200F,
    "endash":                  0x2013,
    "emdash":                  0x2014,
    "horizontalbar":           0x2015,
    "doublevbar":              0x2016,
    "undertie":                0x2017,
    "lsquote":                 0x2018,
    "rsquote":                 0x2019,
    "ldquote":                 0x201C,
    "rdquote":                 0x201D,
    "dagger":                  0x2020,
    "ddagger":                 0x2021,
    "ellipsis":                0x2026,
    "permille":                0x2030,
    "lsaquo":                  0x2039,
    "rsaquo":                  0x203A,
    "overline":                0x203E,
    "interrobang":             0x203D,
    "fraction":                0x2044,

    # ── Braille (U+2800–U+28FF) ────────────────────────────────────────────
    "brailleblank":            0x2800,

    # ── CJK Compatibility (handy aliases) ─────────────────────────────────
    "ideographicspace":        0x3000,
    "ideographicperiod":       0x3002,
    "ideographiccomma":        0x3001,
    "cornerbracketleft":       0x300C,
    "cornerbracketright":      0x300D,
    "whitecornerbracketleft":  0x300E,
    "whitecornerbracketright": 0x300F,
    "wavydash":                0x301C,
    "referencemark":           0x203B,
}

# ────────────────────────────────────────────────────────────────────────────
# SVG helpers
# ────────────────────────────────────────────────────────────────────────────

_SHAPE_TAGS = {"path", "rect", "circle", "ellipse", "polygon", "polyline", "line", "use", "g"}


def has_visible_outlines(svg_bytes: bytes) -> bool:
    """Return True if the SVG bytes contain at least one drawable shape element."""
    try:
        root = ET.fromstring(svg_bytes)
        ns = root.tag.split("}")[0].lstrip("{") if "}" in root.tag else ""
        prefix = f"{{{ns}}}" if ns else ""
        for tag in _SHAPE_TAGS:
            if root.find(f".//{prefix}{tag}") is not None:
                return True
    except Exception:
        pass
    return False


def inkscape_run(args: list[str], stdin_data: Optional[bytes] = None) -> bytes:
    """Run inkscape and return stdout bytes.  stdin_data fed via pipe if given."""
    result = subprocess.run(
        ["inkscape"] + args,
        input=stdin_data,
        capture_output=True,
    )
    if result.returncode != 0:
        # non-fatal — return empty so callers can degrade gracefully
        return b""
    return result.stdout


def process_svg_bytes(raw_svg: bytes) -> bytes:
    """
    Given raw SVG bytes (a single exported glyph):
      1. stroke-to-path  (--actions="select-all;stroke-to-path")
      3. export as plain SVG to stdout
    Returns the processed SVG bytes (falls back to raw_svg on failure).
    """
    # Write to a temp file because inkscape --pipe output for transforms is
    # unreliable across versions; using --export-filename=- is stable on 1.x+
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp_in:
        tmp_in.write(raw_svg)
        tmp_in_path = tmp_in.name

    tmp_out_path = tmp_in_path.replace(".svg", "_out.svg")

    try:
        subprocess.run(
            [
                "inkscape",
                tmp_in_path,
                "--actions=select-all;stroke-to-path",
                "--export-plain-svg",
                "--export-type=svg",
                f"--export-filename={tmp_out_path}",
            ],
            capture_output=True,
        )
        out_path = Path(tmp_out_path)
        if out_path.exists() and out_path.stat().st_size > 0:
            return out_path.read_bytes()
    finally:
        Path(tmp_in_path).unlink(missing_ok=True)
        Path(tmp_out_path).unlink(missing_ok=True)

    return raw_svg  # fallback — use original if processing failed


# ────────────────────────────────────────────────────────────────────────────
# Batch SVG export from drawing.svg  (in-memory)
# Returns: dict[rel_path_str -> svg_bytes]
#   rel_path_str is like "regular/symbol/arrow.svg"
# ────────────────────────────────────────────────────────────────────────────

def _strip_display_none(source: Path) -> Path:
    """
    Write a temp copy of source with all hidden-layer attributes removed so
    Inkscape will render every layer regardless of its visibility state.
    Handles:
      - style="...display:none..."
      - style="...visibility:hidden..."
      - display="none"  attribute
      - visibility="hidden"  attribute
    """
    work = tempfile.NamedTemporaryFile(suffix=".svg", delete=False)
    subprocess.run(
        [
            "xmlstarlet", "ed",
            # Remove display:none from style attributes
            "-u", '//*[contains(@style,"display:none")]/@style',
            "-x", 'concat(substring-before(.,"display:none"), substring-after(.,"display:none"))',
            # Remove visibility:hidden from style attributes
            "-u", '//*[contains(@style,"visibility:hidden")]/@style',
            "-x", 'concat(substring-before(.,"visibility:hidden"), substring-after(.,"visibility:hidden"))',
            # Remove standalone display="none" attributes
            "-d", '//*/@display[.="none"]',
            # Remove standalone visibility="hidden" attributes
            "-d", '//*/@visibility[.="hidden"]',
            str(source),
        ],
        stdout=work,
        check=True,
    )
    work.close()
    return Path(work.name)


def _xsel(work: Path, xpath: str) -> list[str]:
    """Run xmlstarlet sel and return non-empty stripped lines."""
    result = subprocess.run(
        ["xmlstarlet", "sel", "-t", "-m", xpath, "-v", "concat(@id,'|',@*[local-name()='label'])", "-n",
         "--ns", "svg=http://www.w3.org/2000/svg", str(work)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        # retry without namespace declaration (some xmlstarlet builds need it omitted)
        result = subprocess.run(
            ["xmlstarlet", "sel", "-t", "-m", xpath, "-v", "concat(@id,'|',@*[local-name()='label'])", "-n",
             str(work)],
            capture_output=True, text=True,
        )
    return [l for l in result.stdout.splitlines() if l.strip()]


IS_LAYER = '@*[local-name()="groupmode"]="layer"'


def _export_id_to_bytes(work: Path, element_id: str) -> bytes:
    """Export a single element by id from work SVG, return plain SVG bytes."""
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as out_f:
        out_path = out_f.name

    try:
        subprocess.run(
            [
                "inkscape", str(work),
                f"--export-id={element_id}",
                "--export-id-only",
                "--export-area-page",
                "--export-plain-svg",
                "--export-type=svg",
                f"--export-filename={out_path}",
            ],
            capture_output=True,
        )
        p = Path(out_path)
        if p.exists() and p.stat().st_size > 0:
            return p.read_bytes()
    finally:
        Path(out_path).unlink(missing_ok=True)

    return b""


def _collect_layer_svgs(
    work: Path,
    layer_id: str,
    dest_prefix: str,
) -> dict[str, bytes]:
    """
    Mirror of export_paths_from_layer() but returns {rel_path -> raw_bytes}
    instead of writing to disk.
    """
    result: dict[str, bytes] = {}

    # ---- A) Direct labelled non-layer children ----
    direct = _xsel(work, f"//*[@id='{layer_id}']/*[@*[local-name()='label']][not({IS_LAYER})]")
    for line in direct:
        parts = line.split("|", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            continue
        eid, label = parts[0].strip(), parts[1].strip()
        name = label.strip()
        raw = _export_id_to_bytes(work, eid)
        if raw:
            result[f"{dest_prefix}/{name}.svg"] = raw

    # ---- B+C) Child layers ----
    child_layers = _xsel(work, f"//*[@id='{layer_id}']/*[{IS_LAYER}]")
    for line in child_layers:
        parts = line.split("|", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            continue
        cl_id, cl_name = parts[0].strip(), parts[1].strip()
        cl_label = cl_name.lstrip("-").strip()

        cl_paths = _xsel(work, f"//*[@id='{cl_id}']/*[@*[local-name()='label']][not({IS_LAYER})]")
        if cl_paths:
            # B) sublayer has paths
            for pline in cl_paths:
                pparts = pline.split("|", 1)
                if len(pparts) != 2 or not pparts[0] or not pparts[1]:
                    continue
                pid, plabel = pparts[0].strip(), pparts[1].strip()
                name = plabel.strip()
                raw = _export_id_to_bytes(work, pid)
                if raw:
                    result[f"{dest_prefix}/{name}.svg"] = raw
        else:
            # C) empty sublayer — export the layer itself
            raw = _export_id_to_bytes(work, cl_id)
            if raw:
                result[f"{dest_prefix}/{cl_label}.svg"] = raw

    # ---- truly empty layer ----
    if not result:
        r2 = subprocess.run(
            ["xmlstarlet", "sel", "-t", "-v",
             f"//*[@id='{layer_id}']/@*[local-name()='label']", str(work)],
            capture_output=True, text=True,
        )
        layer_label = r2.stdout.strip().lstrip("-")
        raw = _export_id_to_bytes(work, layer_id)
        if raw:
            result[f"{dest_prefix}/{layer_label}.svg"] = raw

    return result


def _matches_filter(name: str, filters: list[str]) -> bool:
    if not filters:
        return True
    nl = name.lower()
    return any(f.lower() in nl for f in filters)


def collect_all_svgs(filter_layers: list[str]) -> dict[str, bytes]:
    """
    Full in-memory equivalent of the bash batch_export.sh.
    Returns {rel_path -> raw_svg_bytes}, rel_path like "regular/symbol/arrow.svg".
    After collecting, applies stroke→path to every SVG in memory.
    """
    print(f"\n{BLUE}[*] Stripping display:none from source{NC}")
    work = _strip_display_none(SOURCE)

    try:
        raw_result: dict[str, bytes] = {}

        # ---- root layers ----
        root_layers = _xsel(work, f"/svg:svg/*[{IS_LAYER}]")
        if not root_layers:
            root_layers = _xsel(work, f"//*[local-name()='svg']/*[{IS_LAYER}]")
        if not root_layers:
            print(f"{RED}[!] Error: No root layers found in {SOURCE}{NC}", file=sys.stderr)
            sys.exit(1)

        # ---- collect Family layer ----
        fam_r = subprocess.run(
            ["xmlstarlet", "sel", "-t", "-v",
             f"//*[{IS_LAYER}][@*[local-name()='label']='Family']/@id", str(work)],
            capture_output=True, text=True,
        )
        family_id = fam_r.stdout.strip()
        family_cats: dict[str, str] = {}  # cat_key -> cat_id

        if family_id:
            print(f"\n{BLUE}[*] Found Family layer — collecting shared glyphs{NC}")
            cat_lines = _xsel(work, f"//*[@id='{family_id}']/*[{IS_LAYER}]")
            for line in cat_lines:
                parts = line.split("|", 1)
                if len(parts) != 2 or not parts[0] or not parts[1]:
                    continue
                cid, cname = parts[0].strip(), parts[1].strip()
                ckey = cname.lstrip("-").strip().lower().replace(" ", "")
                family_cats[ckey] = cid
                print(f"  -> Shared category: {GREEN}{ckey}{NC}")

        if filter_layers:
            print(f"\n{BLUE}[*] Filter active — targeting layers:{NC}")
            for f in filter_layers:
                print(f"   {GREEN}+{NC} {f}")

        print(f"\n{BLUE}[*] Processing weight layers{NC}")
        print(f"{BLUE}------------------------------------------{NC}")

        for line in root_layers:
            parts = line.split("|", 1)
            if len(parts) != 2 or not parts[0] or not parts[1]:
                continue
            root_id, root_name = parts[0].strip(), parts[1].strip()

            if root_name == "Family":
                continue
            if root_name in SKIP_LAYERS:
                print(f"\n{YELLOW}[~] Skipping:{NC} {root_name}")
                continue

            root_folder = root_name.lower()
            print(f"\n{BLUE}[*] Weight:{NC} {GREEN}{root_name}{NC} -> exported/{root_folder}/")
            print(f"{BLUE}------------------------------------------{NC}")

            # Step A — write Family glyphs first (baseline), respecting filter.
            # When a filter is active, only export Family cats that match it.
            # Cats that don't match are skipped here; compile mode falls back to disk.
            for cat_key, cat_id in family_cats.items():
                if not _matches_filter(cat_key, filter_layers):
                    print(f"\n  {YELLOW}[~] Family->{cat_key}{NC} filtered out (skipping)")
                    continue
                print(f"\n  {BLUE}[F] Family->{cat_key}{NC} (shared)")
                svgs = _collect_layer_svgs(work, cat_id, f"{root_folder}/{cat_key}")
                raw_result.update(svgs)

            # Step B — weight-specific layers (overrides Family)
            child_lines = _xsel(work, f"//*[@id='{root_id}']/*[{IS_LAYER}]")
            for cline in child_lines:
                cparts = cline.split("|", 1)
                if len(cparts) != 2 or not cparts[0] or not cparts[1]:
                    continue
                child_id, child_name = cparts[0].strip(), cparts[1].strip()
                child_folder = child_name.lstrip("-").strip().lower().replace(" ", "")

                if not _matches_filter(child_folder, filter_layers):
                    print(f"\n  {YELLOW}[~] Filtered out:{NC} {child_folder}")
                    continue

                print(f"\n  {BLUE}[>] {child_folder}{NC} (weight-specific, overrides Family)")
                svgs = _collect_layer_svgs(work, child_id, f"{root_folder}/{child_folder}")
                raw_result.update(svgs)

        # ---- apply stroke→path to everything in memory ----
        print(f"\n{BLUE}[*] Processing: stroke→path ({len(raw_result)} SVGs){NC}")
        processed: dict[str, bytes] = {}
        for rel_path, raw in raw_result.items():
            proc = process_svg_bytes(raw)
            processed[rel_path] = proc
            stem = Path(rel_path).stem
            print(f"   -> {GREEN}{rel_path}{NC}")

        return processed

    finally:
        Path(work).unlink(missing_ok=True)


# ────────────────────────────────────────────────────────────────────────────
# Export mode — write all SVGs to disk in one pass
# ────────────────────────────────────────────────────────────────────────────

def cmd_export(filter_layers: list[str]) -> None:
    svgs = collect_all_svgs(filter_layers)

    # ---- clean up old exported SVGs before writing new ones ----
    if DEST_DIR.exists():
        import shutil
        print(f"\n{YELLOW}[~] Removing old exports:{NC} {DEST_DIR}")
        shutil.rmtree(DEST_DIR)
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n{BLUE}[*] Writing {len(svgs)} SVG(s) to disk…{NC}")
    for rel_path, data in svgs.items():
        dest = DEST_DIR / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)

    print(f"\n{BLUE}------------------------------------------{NC}")
    print(f"{GREEN}[+] Export complete!{NC}")
    print(f"    {DEST_DIR}")
    print(f"{BLUE}------------------------------------------{NC}")


# ────────────────────────────────────────────────────────────────────────────
# Font compile helpers
# ────────────────────────────────────────────────────────────────────────────

def resolve_codepoint(stem: str):
    """
    Priority order:
      1. .notdef                          -> sentinel -1
      2. Single printable ASCII char      -> its ordinal
      3. Known ASCII name in map          -> mapped codepoint
      4. Hex string  U+XXXX  or  XXXX    -> parsed codepoint  (for CJK / mapped dirs)
      5. Single non-ASCII Unicode char    -> its ordinal       (e.g. a literal 你)
      6. Everything else                  -> None  (caller assigns PUA)
    """
    if stem == ".notdef":
        return -1, ".notdef  (special)"

    # Single printable ASCII character
    if len(stem) == 1 and 0x20 <= ord(stem) <= 0x7E:
        cp = ord(stem)
        return cp, f"U+{cp:04X}  (ASCII '{stem}')"

    # Known ASCII name
    cp = ASCII_NAME_MAP.get(stem.lower())
    if cp is not None:
        return cp, f"U+{cp:04X}  (ASCII name '{stem}')"

    # Known Unicode name (arrows, math, symbols, etc.)
    cp = UNICODE_NAME_MAP.get(stem.lower())
    if cp is not None:
        char_repr = chr(cp)
        return cp, f"U+{cp:04X}  (Unicode '{char_repr}'  '{stem}')"

    # Hex string: "U+4E2D" or "4E2D" (4–6 hex digits)
    hex_stem = stem.upper().lstrip("U+").lstrip("0") or "0"
    if 1 <= len(hex_stem) <= 6 and all(c in "0123456789ABCDEF" for c in hex_stem):
        # Only treat as hex if the original stem was a pure hex/U+ string,
        # not a normal word that happens to be hex (e.g. "add", "bad", "beef").
        # Heuristic: original stem must start with "U+" OR be all hex digits with
        # no lowercase letters (since real words are lowercase).
        is_u_prefix  = stem.upper().startswith("U+")
        is_pure_hex  = stem == stem.upper() and len(stem) >= 4
        if is_u_prefix or is_pure_hex:
            cp = int(hex_stem, 16)
            char_repr = chr(cp) if cp > 0x7E else repr(chr(cp))
            return cp, f"U+{cp:04X}  (hex '{char_repr}')"

    # Single non-ASCII Unicode character (e.g. literal CJK glyph as filename)
    if len(stem) == 1 and ord(stem) > 0x7E:
        cp = ord(stem)
        return cp, f"U+{cp:04X}  (char '{stem}')"

    return None, None


def center_glyph(glyph, target_width: int = 500) -> None:
    bbox = glyph.boundingBox()
    if bbox is None or bbox == (0, 0, 0, 0):
        glyph.width = target_width
        return
    xmin, _, xmax, _ = bbox
    glyph_w  = xmax - xmin
    offset_x = (target_width - glyph_w) / 2 - xmin
    glyph.transform((1, 0, 0, 1, offset_x, 0))
    glyph.width = target_width


def make_glyph(font, codepoint: int, stem: str):
    if codepoint == -1:
        return font.createChar(-1, ".notdef")
    return font.createChar(codepoint, f"uni{codepoint:04X}")


def _sorted_svgs_from_dict(
    svgs: dict[str, bytes],
    prefix: str,            # e.g. "regular/symbol"
) -> list[tuple[str, bytes]]:
    """Return (stem, bytes) pairs sorted alphabetically for a given prefix."""
    matches = [(k, v) for k, v in svgs.items() if k.startswith(prefix + "/")]
    matches.sort(key=lambda x: Path(x[0]).stem.lower())
    return [(Path(k).stem, v) for k, v in matches]


def build_weight_from_memory(
    svgs: dict[str, bytes],
    folder_name: str,
    style_name: str,
    os2_weight: int,
    version: str,
    write_to_disk: bool = True,
) -> tuple[bytes, bytes]:
    """
    Compile one font weight from in-memory SVGs.
    Always returns (ttf_bytes, woff2_bytes).
    Also writes TTF+WOFF2 to TTF_DIR when write_to_disk=True.
    """
    ff = _ff
    font = ff.font()
    font.familyname = FAMILY_NAME
    font.fullname   = f"{FAMILY_NAME} {style_name}"
    font.fontname   = f"{FAMILY_NAME.replace(' ', '')}-{style_name}"
    font.version    = version
    font.weight     = style_name
    font.os2_weight = os2_weight
    if os2_weight >= 600:
        font.macstyle     = 0b00000001
        font.os2_stylemap = 0b00100000
    font.ascent  = 800
    font.descent = 200

    safe_style = style_name.replace(" ", "")
    ttf_filename   = f"MamboFont-{safe_style}_v{version}.ttf"
    woff2_filename = f"MamboFont-{safe_style}_v{version}.woff2"

    print(f"\n{BLUE}=========================================={NC}")
    print(f" Weight:  {GREEN}{style_name}{NC}  (OS/2 {os2_weight})")
    if write_to_disk:
        print(f" Outputs: {ttf_filename}")
        print(f"          {woff2_filename}")
    else:
        print(f" Mode:    in-memory only (release)")
    print(f"{BLUE}=========================================={NC}")

    pua_counter = 0xE000

    def import_svg_bytes(glyph, data: bytes) -> None:
        """
        Write data to a temp file, import into glyph, remove temp file.
        Calls correctDirection() after import to fix winding order — SVG uses
        even-odd fill by default but fonts require non-zero winding, so without
        this overlapping paths produce holes in some renderers.
        """
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tf:
            tf.write(data)
            tf_path = tf.name
        try:
            glyph.importOutlines(tf_path)
            glyph.removeOverlap()
            glyph.correctDirection()
        finally:
            Path(tf_path).unlink(missing_ok=True)

    # ---- SCAN subdirs ----
    for sub in SCAN_SUBDIRS:
        prefix = f"{folder_name}/{sub}"
        items = _sorted_svgs_from_dict(svgs, prefix)
        if not items:
            print(f"\n{RED}[!] Not found, skipping:{NC} {sub}")
            continue

        print(f"\n{BLUE}[*] Scan:{NC} {sub}  ({len(items)} glyphs)")
        for stem, data in items:
            codepoint, slot_label = resolve_codepoint(stem)
            if codepoint is None:
                codepoint  = pua_counter
                slot_label = f"U+{codepoint:04X}  (PUA)"
                pua_counter += 1
            glyph = make_glyph(font, codepoint, stem)
            if has_visible_outlines(data):
                import_svg_bytes(glyph, data)
                center_glyph(glyph)
            else:
                glyph.width = 500
            print(f"   -> {slot_label}  {GREEN}{stem}{NC}")

    # ---- Full-width PUA subdirs (icons, ligatures — always PUA) ----
    for sub in FULLWIDTH_PUA:
        prefix = f"{folder_name}/{sub}"
        items = _sorted_svgs_from_dict(svgs, prefix)
        if not items:
            print(f"\n{RED}[!] Not found, skipping:{NC} {sub}")
            continue

        print(f"\n{BLUE}[*] Full-width PUA:{NC} {sub}  ({len(items)} glyphs)")
        for stem, data in items:
            # Force PUA regardless of what resolve_codepoint would return
            codepoint  = pua_counter
            slot_label = f"U+{codepoint:04X}  (PUA)"
            pua_counter += 1
            glyph = make_glyph(font, codepoint, stem)
            if has_visible_outlines(data):
                import_svg_bytes(glyph, data)
            glyph.width = 1000
            print(f"   -> {slot_label}  {GREEN}{stem}{NC}")

    # ---- Full-width mapped subdirs (CJK etc. — real Unicode codepoints) ----
    for sub in FULLWIDTH_MAPPED:
        prefix = f"{folder_name}/{sub}"
        items = _sorted_svgs_from_dict(svgs, prefix)
        if not items:
            print(f"\n{RED}[!] Not found, skipping:{NC} {sub}")
            continue

        print(f"\n{BLUE}[*] Full-width mapped:{NC} {sub}  ({len(items)} glyphs)")
        for stem, data in items:
            codepoint, slot_label = resolve_codepoint(stem)
            if codepoint is None:
                # Fallback to PUA if stem can't be resolved (shouldn't happen for CJK)
                codepoint  = pua_counter
                slot_label = f"U+{codepoint:04X}  (PUA fallback — check stem '{stem}')"
                pua_counter += 1
                print(f"   {YELLOW}[~] Warning: could not resolve '{stem}' — assigned PUA{NC}")
            glyph = make_glyph(font, codepoint, stem)
            if has_visible_outlines(data):
                import_svg_bytes(glyph, data)
            glyph.width = 1000
            print(f"   -> {slot_label}  {GREEN}{stem}{NC}")

    pua_used = pua_counter - 0xE000
    if pua_used:
        print(f"\n{BLUE}[i] PUA slots used:{NC} {pua_used}  (U+E000 – U+{pua_counter - 1:04X})")

    # Generate to temp files so we can read back as bytes
    with tempfile.NamedTemporaryFile(suffix=".ttf",   delete=False) as t1, \
         tempfile.NamedTemporaryFile(suffix=".woff2", delete=False) as t2:
        tmp_ttf   = t1.name
        tmp_woff2 = t2.name

    try:
        font.generate(tmp_ttf)
        font.generate(tmp_woff2)
        ttf_bytes   = Path(tmp_ttf).read_bytes()
        woff2_bytes = Path(tmp_woff2).read_bytes()
    finally:
        Path(tmp_ttf).unlink(missing_ok=True)
        Path(tmp_woff2).unlink(missing_ok=True)

    if write_to_disk:
        TTF_DIR.mkdir(exist_ok=True)
        (TTF_DIR / ttf_filename).write_bytes(ttf_bytes)
        (TTF_DIR / woff2_filename).write_bytes(woff2_bytes)
        print(f"\n{GREEN}[+] Generated TTF:{NC}   {ttf_filename}")
        print(f"{GREEN}[+] Generated WOFF2:{NC} {woff2_filename}")
    else:
        print(f"\n{GREEN}[+] Compiled TTF:{NC}   {ttf_filename}  ({len(ttf_bytes):,} bytes, in memory)")
        print(f"{GREEN}[+] Compiled WOFF2:{NC} {woff2_filename}  ({len(woff2_bytes):,} bytes, in memory)")

    return ttf_bytes, woff2_bytes


# ────────────────────────────────────────────────────────────────────────────
# Compile mode
# ────────────────────────────────────────────────────────────────────────────

def _load_disk_svgs(folder_name: str) -> dict[str, bytes]:
    """
    Load all SVGs from DEST_DIR/<folder_name>/ into a dict keyed by rel_path.
    Returns empty dict if the folder doesn't exist.
    """
    base = DEST_DIR / folder_name
    if not base.exists():
        return {}
    result: dict[str, bytes] = {}
    for svg_file in base.rglob("*.svg"):
        rel = svg_file.relative_to(DEST_DIR)
        result[str(rel)] = svg_file.read_bytes()
    return result


def cmd_compile(version: str, filter_layers: list[str]) -> None:
    if _ff is None:
        print(f"{RED}[!] Error: FontForge Python bindings not found.{NC}")
        print("    Please run: 'sudo pacman -S fontforge'")
        sys.exit(1)

    # When a filter is active:
    #   1. Export only the filtered layers fresh (in-memory, no disk write).
    #   2. Load the rest from disk (DEST_DIR) as the base.
    #   3. Overlay the fresh SVGs on top so filtered layers always win.
    # When no filter: export everything fresh as before.
    fresh_svgs = collect_all_svgs(filter_layers)

    if filter_layers:
        print(f"\n{BLUE}[*] Merging fresh SVGs with disk cache for unfiltered layers{NC}")
        merged: dict[str, bytes] = {}
        for folder_name, _, _ in WEIGHTS:
            disk = _load_disk_svgs(folder_name)
            if not disk:
                print(f"  {YELLOW}[~] No disk cache for weight '{folder_name}' — only fresh data will be used{NC}")
            merged.update(disk)          # disk first (lower priority)
        merged.update(fresh_svgs)        # fresh on top (higher priority)
        svgs = merged
        print(f"  -> {len(svgs)} total SVGs ({len(fresh_svgs)} fresh + {len(merged) - len(fresh_svgs)} from disk)")
    else:
        svgs = fresh_svgs

    print(f"\n{BLUE}------------------------------------------{NC}")
    print(f" Family:  {GREEN}{FAMILY_NAME}{NC}")
    print(f" Version: {GREEN}{version}{NC}")
    print(f" Weights: {GREEN}{', '.join(w[1] for w in WEIGHTS)}{NC}")
    print(f"{BLUE}------------------------------------------{NC}")

    for folder_name, style_name, os2_weight in WEIGHTS:
        if not any(k.startswith(f"{folder_name}/") for k in svgs):
            print(f"\n{RED}[!] No SVGs found for weight '{folder_name}', skipping{NC}")
            continue
        build_weight_from_memory(svgs, folder_name, style_name, os2_weight, version)

    print(f"\n{BLUE}------------------------------------------{NC}")
    print(f"{GREEN}[+] All weights compiled successfully (TTF & WOFF2)!{NC}")
    print(f"{BLUE}------------------------------------------{NC}")



# ────────────────────────────────────────────────────────────────────────────
# Release mode
# ────────────────────────────────────────────────────────────────────────────

def _check_tool(name: str) -> None:
    import shutil
    if shutil.which(name) is None:
        print(f"{RED}[!] Error: '{name}' is not installed.{NC}", file=sys.stderr)
        sys.exit(1)


def _zip_in_memory(named_files: list[tuple[str, bytes]]) -> bytes:
    """Build a zip archive in memory. named_files: [(arcname, data), ...]"""
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for arcname, data in named_files:
            zf.writestr(arcname, data)
    return buf.getvalue()


def _check_git_auth() -> None:
    """Verify all CLI tools are present and gh is authenticated. Call before any heavy work."""
    _check_tool("gh")
    _check_tool("git")
    _check_tool("nvim")
    r = subprocess.run(["gh", "auth", "status"], capture_output=True)
    if r.returncode != 0:
        print(f"{RED}[!] Error: Not authenticated with GitHub CLI. Run 'gh auth login'{NC}", file=sys.stderr)
        sys.exit(1)


def _release_exists(tag_name: str) -> bool:
    """Return True if a GitHub release with this tag already exists."""
    r = subprocess.run(
        ["gh", "release", "view", tag_name],
        capture_output=True,
    )
    return r.returncode == 0


def _fetch_release_notes(tag_name: str) -> str:
    """Fetch the body of an existing GitHub release. Returns empty string on failure."""
    r = subprocess.run(
        ["gh", "release", "view", tag_name, "--json", "body", "--jq", ".body"],
        capture_output=True, text=True,
    )
    return r.stdout.strip() if r.returncode == 0 else ""


def _open_notes_in_nvim(seed_text: str = "") -> str:
    """
    Open nvim for the user to write/edit release notes.
    seed_text pre-populates the buffer (used for amend-style edits).
    Returns the final notes string (comment lines stripped, empty lines collapsed).
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, prefix="mambo_release_"
    ) as nf:
        if seed_text:
            nf.write(seed_text + "\n")
        nf.write("# Write your release notes above. Lines starting with # are ignored.\n")
        nf.write("# Leave empty to auto-generate.\n")
        notes_path = nf.name

    try:
        subprocess.run(["nvim", notes_path], check=True)
        raw = Path(notes_path).read_text()
    finally:
        Path(notes_path).unlink(missing_ok=True)

    lines = [l for l in raw.splitlines() if not l.startswith("#")]
    return "\n".join(lines).strip()


def cmd_release(version: str) -> None:
    if _ff is None:
        print(f"{RED}[!] Error: FontForge Python bindings not found.{NC}")
        print("    Please run: 'sudo pacman -S fontforge'")
        sys.exit(1)

    # ── auth + tool checks before any expensive work ──────────────────────────
    _check_git_auth()

    tag_name      = f"v{version}"
    release_title = f"Mambo Font {tag_name}"

    # ── check if release already exists, offer to unrelease first ────────────
    if _release_exists(tag_name):
        print(f"\n{YELLOW}[!] Release {tag_name} already exists on GitHub.{NC}")
        print(f"    Unreleasing first allows you to amend it with new assets + notes.")
        ans = input(f"    Unrelease {tag_name} and continue? [y/N] ").strip().lower()
        if ans != "y":
            print(f"{YELLOW}[~] Aborting — existing release left untouched.{NC}")
            sys.exit(0)
        _amend_seed = _fetch_release_notes(tag_name)
        cmd_unrelease(version, _skip_auth_check=True)
    else:
        _amend_seed = ""

    # ── compile all weights fully in memory (no disk write) ──────────────────
    svgs = collect_all_svgs([])   # no filter — full export

    print(f"\n{BLUE}------------------------------------------{NC}")
    print(f" Family:  {GREEN}{FAMILY_NAME}{NC}")
    print(f" Version: {GREEN}{version}{NC}")
    print(f" Tag:     {GREEN}{tag_name}{NC}")
    print(f" Weights: {GREEN}{', '.join(w[1] for w in WEIGHTS)}{NC}")
    print(f"{BLUE}------------------------------------------{NC}")

    # {filename -> bytes} for all generated font files
    font_files: dict[str, bytes] = {}

    for folder_name, style_name, os2_weight in WEIGHTS:
        if not any(k.startswith(f"{folder_name}/") for k in svgs):
            print(f"\n{RED}[!] No SVGs found for weight '{folder_name}', skipping{NC}")
            continue
        ttf_bytes, woff2_bytes = build_weight_from_memory(
            svgs, folder_name, style_name, os2_weight, version,
            write_to_disk=False,
        )
        safe_style = style_name.replace(" ", "")
        font_files[f"MamboFont-{safe_style}_v{version}.ttf"]   = ttf_bytes
        font_files[f"MamboFont-{safe_style}_v{version}.woff2"] = woff2_bytes

    if not font_files:
        print(f"{RED}[!] No font files compiled, aborting release.{NC}", file=sys.stderr)
        sys.exit(1)

    # ── build zip archives in memory ─────────────────────────────────────────
    ttf_pairs   = [(n, d) for n, d in font_files.items() if n.endswith(".ttf")]
    woff2_pairs = [(n, d) for n, d in font_files.items() if n.endswith(".woff2")]

    ttf_zip_name   = f"MamboFont_v{version}_ttf.zip"
    woff2_zip_name = f"MamboFont_v{version}_woff2.zip"
    ttf_zip_bytes   = _zip_in_memory(ttf_pairs)
    woff2_zip_bytes = _zip_in_memory(woff2_pairs)

    print(f"\n{BLUE}------------------------------------------{NC}")
    print(f" Target: {GREEN}{tag_name}{NC}")
    print(f" TTF Files:")
    for n, _ in ttf_pairs:
        print(f"   {GREEN}+{NC} {n}")
    print(f" WOFF2 Files:")
    for n, _ in woff2_pairs:
        print(f"   {GREEN}+{NC} {n}")
    print(f" -> Created Archive: {ttf_zip_name}")
    print(f" -> Created Archive: {woff2_zip_name}")
    print(f"{BLUE}------------------------------------------{NC}")

    # ── tag commit ───────────────────────────────────────────────────────────
    print(f"\n{BLUE}[*] Tagging commit: {tag_name}...{NC}")
    subprocess.run(
        ["git", "tag", "-a", tag_name, "-m", f"Mambo Font release version {version}"],
        check=True,
    )
    subprocess.run(["git", "push", "origin", tag_name], capture_output=True, check=True)

    # ── open nvim for release notes ───────────────────────────────────────────
    notes = _open_notes_in_nvim(seed_text=_amend_seed)
    if not notes:
        notes = f"Mambo Font {version}"
        print(f"{BLUE}[i] No notes provided — using auto-generated message.{NC}")

    # ── write all assets to a temp dir, run gh release create, clean up ───────
    all_assets: list[tuple[str, bytes]] = (
        list(font_files.items())
        + [(ttf_zip_name, ttf_zip_bytes), (woff2_zip_name, woff2_zip_bytes)]
    )
    total = len(all_assets)

    with tempfile.TemporaryDirectory(prefix="mambo_release_") as tmp_dir:
        asset_paths: list[str] = []
        for filename, data in all_assets:
            p = Path(tmp_dir) / filename
            p.write_bytes(data)
            asset_paths.append(str(p))

        print(f"{BLUE}[*] Publishing release to GitHub ({total} files)...{NC}")
        subprocess.run(
            [
                "gh", "release", "create", tag_name,
                *asset_paths,
                "--title", release_title,
                "--notes", notes,
            ],
            check=True,
        )
    # temp dir and all files inside are deleted here automatically

    print(f"\n{BLUE}------------------------------------------{NC}")
    print(f"{GREEN}[+] Release complete!{NC}")
    print(f"{BLUE}------------------------------------------{NC}")


# ────────────────────────────────────────────────────────────────────────────
# Unrelease mode
# ────────────────────────────────────────────────────────────────────────────

def cmd_unrelease(version: str, _skip_auth_check: bool = False) -> None:
    """
    Delete a GitHub release and its tag — both remote and local.
    When called from cmd_release (amend flow), _skip_auth_check=True skips
    redundant tool/auth validation.
    """
    if not _skip_auth_check:
        _check_git_auth()

    tag_name = f"v{version}"

    # ── confirm the release actually exists ───────────────────────────────────
    if not _release_exists(tag_name):
        print(f"{RED}[!] No GitHub release found for {tag_name}. Nothing to do.{NC}", file=sys.stderr)
        sys.exit(1)

    print(f"\n{BLUE}------------------------------------------{NC}")
    print(f" Unreleasing: {GREEN}{tag_name}{NC}")
    print(f"{BLUE}------------------------------------------{NC}")

    # ── delete the GitHub release (keeps tag for now) ────────────────────────
    print(f"\n{BLUE}[*] Deleting GitHub release {tag_name}...{NC}")
    subprocess.run(["gh", "release", "delete", tag_name, "--yes"], check=True)

    # ── delete remote tag ─────────────────────────────────────────────────────
    print(f"{BLUE}[*] Deleting remote tag {tag_name}...{NC}")
    r = subprocess.run(
        ["git", "push", "origin", f":refs/tags/{tag_name}"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        # Non-fatal: tag may not exist on remote (e.g. never pushed)
        print(f"  {YELLOW}[~] Remote tag not found or already deleted.{NC}")

    # ── delete local tag ──────────────────────────────────────────────────────
    print(f"{BLUE}[*] Deleting local tag {tag_name}...{NC}")
    r = subprocess.run(["git", "tag", "-d", tag_name], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  {YELLOW}[~] Local tag not found or already deleted.{NC}")

    print(f"\n{BLUE}------------------------------------------{NC}")
    print(f"{GREEN}[+] Unrelease complete!{NC}  {tag_name} removed.")
    print(f"{BLUE}------------------------------------------{NC}")

# ────────────────────────────────────────────────────────────────────────────
# Entry point
# ────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mambo_font.py",
        description="Export SVG layers and/or compile Mambo Font weights.",
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    # export sub-command
    p_export = sub.add_parser("export", help="Export processed SVGs to disk")
    p_export.add_argument(
        "filters", nargs="*",
        help="Optional layer name filters (case-insensitive, partial match)",
    )

    # compile sub-command
    p_compile = sub.add_parser(
        "compile",
        help="Compile font weights (export in-memory, no SVGs written to disk)",
    )
    p_compile.add_argument("version", help="Font version string, e.g. 1.0")
    p_compile.add_argument(
        "filters", nargs="*",
        help="Optional layer name filters (case-insensitive, partial match)",
    )

    # release sub-command
    p_release = sub.add_parser(
        "release",
        help="Compile all weights in-memory and publish a GitHub release",
    )
    p_release.add_argument("version", help="Font version string, e.g. 1.2.3")

    # unrelease sub-command
    p_unrelease = sub.add_parser(
        "unrelease",
        help="Delete a GitHub release and its tag (local + remote)",
    )
    p_unrelease.add_argument("version", help="Version to delete, e.g. 1.2.3")

    args = parser.parse_args()

    if args.mode == "export":
        cmd_export(args.filters)
    elif args.mode == "compile":
        cmd_compile(args.version, args.filters)
    elif args.mode == "release":
        cmd_release(args.version)
    elif args.mode == "unrelease":
        cmd_unrelease(args.version)


if __name__ == "__main__":
    main()