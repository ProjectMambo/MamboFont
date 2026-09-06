"""Deterministic source geometry for Mambo Font.

Glyphs are straight centre-line paths.  The build script expands the same
paths at four stroke widths, which keeps the family related without keeping
four drawings in sync.
"""

from unicodedata import normalize

from sources.geometry import combine, glyph, loop, path, transform


L, R, C = 100, 400, 250
CAP, XH, MID, XMID, DESC = 640, 400, 320, 200, -140


def ring(left=L, right=R, bottom=0, top=CAP):
    return loop((left, bottom), (right, bottom), (right, top), (left, top))


def c_shape(left=L, right=R, bottom=0, top=CAP):
    return path((right, top), (left, top), (left, bottom), (right, bottom))


def bowl(left=L, right=R, bottom=0, top=XH):
    return ring(left, right, bottom, top)


# Base ASCII.  Repeated structures are intentional visual grammar, not copied
# outlines: changing a global metric or weight updates every instance.
GLYPHS = {
    " ": glyph(),
    "A": glyph(path((80, 0), (190, CAP), (310, CAP), (420, 0)), path((135, MID), (365, MID))),
    "B": glyph(
        path((L, 0), (L, CAP)),
        path((L, CAP), (360, CAP), (360, MID), (L, MID)),
        path((L, MID), (R, MID), (R, 0), (L, 0)),
    ),
    "C": glyph(c_shape()),
    "D": glyph(path((L, 0), (L, CAP)), path((L, CAP), (330, CAP), (R, MID), (R, 0), (L, 0))),
    "E": glyph(path((L, 0), (L, CAP)), path((L, CAP), (R, CAP)), path((L, MID), (350, MID)), path((L, 0), (R, 0))),
    "F": glyph(path((L, 0), (L, CAP)), path((L, CAP), (R, CAP)), path((L, MID), (350, MID))),
    "G": glyph(c_shape(), path((R, 260), (300, 260)), path((R, 260), (R, 0))),
    "H": glyph(path((L, 0), (L, CAP)), path((R, 0), (R, CAP)), path((L, MID), (R, MID))),
    "I": glyph(path((L, CAP), (R, CAP)), path((C, 0), (C, CAP)), path((L, 0), (R, 0))),
    "J": glyph(path((L, CAP), (R, CAP), (R, 0), (L, 0), (L, 140))),
    "K": glyph(path((L, 0), (L, CAP)), path((R, CAP), (L, MID)), path((L, MID), (R, 0))),
    "L": glyph(path((L, CAP), (L, 0), (R, 0))),
    "M": glyph(path((L, 0), (L, CAP)), path((L, CAP), (C, 330)), path((C, 330), (R, CAP)), path((R, CAP), (R, 0))),
    "N": glyph(path((L, 0), (L, CAP)), path((L, CAP), (R, 0)), path((R, 0), (R, CAP))),
    "O": glyph(ring()),
    "P": glyph(path((L, 0), (L, CAP)), path((L, CAP), (R, CAP), (R, MID), (L, MID))),
    "Q": glyph(ring(), path((285, 150), (420, -35))),
    "R": glyph(
        path((L, 0), (L, CAP)),
        path((L, CAP), (R, CAP), (R, MID), (L, MID)),
        path((290, MID), (410, 0)),
    ),
    "S": glyph(path((R, CAP), (L, CAP), (L, MID), (R, MID), (R, 0), (L, 0))),
    "T": glyph(path((70, CAP), (430, CAP)), path((C, CAP), (C, 0))),
    "U": glyph(path((L, CAP), (L, 0), (R, 0), (R, CAP))),
    "V": glyph(path((75, CAP), (205, 0), (295, 0), (425, CAP))),
    "W": glyph(path((70, CAP), (130, 0)), path((130, 0), (C, 260)), path((C, 260), (370, 0)), path((370, 0), (430, CAP))),
    "X": glyph(path((85, CAP), (415, 0)), path((415, CAP), (85, 0))),
    "Y": glyph(path((L, CAP), (L, MID), (R, MID), (R, CAP)), path((C, MID), (C, 0))),
    "Z": glyph(path((L, CAP), (R, CAP)), path((R, CAP), (L, 0)), path((L, 0), (R, 0))),

    "a": glyph(path((L, XH), (R, XH), (R, 0), (L, 0), (L, 140)), path((L, 140), (R, XH))),
    "b": glyph(path((L, 0), (L, CAP)), bowl(left=L, right=R, bottom=0, top=XH)),
    "c": glyph(c_shape(bottom=0, top=XH)),
    "d": glyph(bowl(left=L, right=R, bottom=0, top=XH), path((R, 0), (R, CAP))),
    "e": glyph(c_shape(bottom=0, top=XH), path((L, XMID), (R, XMID))),
    "f": glyph(path((R, CAP), (C, CAP), (C, 0)), path((L, XH), (R, XH))),
    "g": glyph(bowl(left=L, right=R, bottom=0, top=XH), path((R, XH), (R, DESC), (L, DESC), (L, -80))),
    "h": glyph(path((L, 0), (L, CAP)), path((L, XH), (R, XH), (R, 0))),
    "i": glyph(path((C, 0), (C, 330)), dots=((C, 415, 0.9),)),
    "j": glyph(path((R, 300), (R, DESC), (L, DESC), (L, -80)), dots=((R, 390, 0.9),)),
    "k": glyph(path((L, 0), (L, CAP)), path((R, XH), (L, XMID)), path((L, XMID), (R, 0))),
    "l": glyph(path((C, CAP), (C, 0), (R, 0))),
    "m": glyph(path((L, 0), (L, XH)), path((L, XH), (C, XMID)), path((C, XMID), (R, XH)), path((R, XH), (R, 0))),
    "n": glyph(path((L, 0), (L, XH)), path((L, XH), (R, 0)), path((R, 0), (R, XH))),
    "o": glyph(bowl(top=XH)),
    "p": glyph(path((L, DESC), (L, XH)), bowl(left=L, right=R, bottom=0, top=XH)),
    "q": glyph(bowl(left=L, right=R, bottom=0, top=XH), path((R, XH), (R, DESC))),
    "r": glyph(path((L, 0), (L, XH), (R, XH), (R, 310))),
    "s": glyph(path((R, XH), (L, XH)), path((L, XH), (R, 0)), path((R, 0), (L, 0))),
    "t": glyph(path((C, 560), (C, 0)), path((L, XH), (R, XH))),
    "u": glyph(path((L, XH), (L, 0), (R, 0), (R, XH))),
    "v": glyph(path((85, XH), (205, 0), (295, 0), (415, XH))),
    "w": glyph(path((L, XH), (L, 0)), path((L, 0), (C, XMID)), path((C, XMID), (R, 0)), path((R, 0), (R, XH))),
    "x": glyph(path((90, XH), (410, 0)), path((410, XH), (90, 0))),
    "y": glyph(path((L, XH), (L, 0), (R, 0), (R, XH)), path((R, 0), (R, DESC), (L, DESC), (L, -80))),
    "z": glyph(path((L, XH), (R, XH)), path((R, XH), (L, 0)), path((L, 0), (R, 0))),

    "0": glyph(ring(), path((135, 80), (365, 560))),
    "1": glyph(path((150, 520), (C, CAP)), path((C, CAP), (C, 0)), path((L, 0), (R, 0))),
    "2": glyph(path((L, CAP), (R, CAP), (R, 420)), path((R, 420), (L, 0)), path((L, 0), (R, 0))),
    "3": glyph(path((L, CAP), (R, CAP), (R, 0), (L, 0)), path((L, MID), (R, MID))),
    "4": glyph(path((L, CAP), (L, MID), (R, MID)), path((R, CAP), (R, 0))),
    "5": glyph(path((R, CAP), (L, CAP), (L, MID), (R, MID)), path((R, MID), (C, 0)), path((C, 0), (L, 0))),
    "6": glyph(path((R, CAP), (L, CAP), (L, 0), (R, 0), (R, MID), (L, MID))),
    "7": glyph(path((L, CAP), (R, CAP)), path((R, CAP), (170, 0))),
    "8": glyph(ring(left=L, right=R, bottom=MID, top=CAP), ring(left=L, right=R, bottom=0, top=MID)),
    "9": glyph(path((L, 0), (R, 0), (R, CAP), (L, CAP), (L, MID), (R, MID))),

    "!": glyph(path((C, 220), (C, CAP)), dots=((C, 45, 1.0),)),
    '"': glyph(path((190, 500), (190, CAP)), path((310, 500), (310, CAP))),
    "#": glyph(path((150, 0), (150, CAP)), path((350, 0), (350, CAP)), path((70, 210), (430, 210)), path((70, 430), (430, 430))),
    "$": glyph(path((R, CAP), (L, CAP), (L, MID), (R, MID), (R, 0), (L, 0)), path((C, 700), (C, -60))),
    "%": glyph(ring(90, 210, 440, 620), path((120, 0), (380, CAP)), ring(290, 410, 20, 200)),
    "&": glyph(path((R, CAP), (L, CAP), (L, 420), (R, 0), (L, 0), (L, 170), (R, 500)), path((260, 260), (420, 80))),
    "'": glyph(path((C, 500), (C, CAP))),
    "(": glyph(path((340, CAP), (220, CAP), (220, 540), (160, 540), (160, 100), (220, 100), (220, 0), (340, 0))),
    ")": glyph(path((160, CAP), (280, CAP), (280, 540), (340, 540), (340, 100), (280, 100), (280, 0), (160, 0))),
    "*": glyph(path((C, 180), (C, 500)), path((110, 420), (390, 260)), path((390, 420), (110, 260))),
    "+": glyph(path((C, 120), (C, 520)), path((70, MID), (430, MID))),
    ",": glyph(path((C, 70), (C, -20), (205, -80))),
    "-": glyph(path((120, MID), (380, MID))),
    ".": glyph(dots=((C, 45, 1.0),)),
    "/": glyph(path((90, 0), (410, CAP))),
    ":": glyph(dots=((C, 105, 0.9), (C, 385, 0.9))),
    ";": glyph(path((C, 120), (C, 20), (205, -60)), dots=((C, 385, 0.9),)),
    "<": glyph(path((390, 560), (110, MID), (390, 80))),
    "=": glyph(path((100, 220), (400, 220)), path((100, 420), (400, 420))),
    ">": glyph(path((110, 560), (390, MID), (110, 80))),
    "?": glyph(path((L, CAP), (R, CAP), (R, 450), (C, MID), (C, 220)), dots=((C, 45, 1.0),)),
    "@": glyph(ring(70, 430, -20, 660), ring(170, 340, 180, 460), path((340, 180), (340, 460), (410, 460), (410, 130), (360, 130), (360, 80))),
    "[": glyph(path((340, CAP), (170, CAP), (170, 0), (340, 0))),
    "\\": glyph(path((90, CAP), (410, 0))),
    "]": glyph(path((160, CAP), (330, CAP), (330, 0), (160, 0))),
    "^": glyph(path((100, 400), (C, CAP), (400, 400))),
    "_": glyph(path((70, -50), (430, -50))),
    "`": glyph(path((C, 500), (190, CAP))),
    "{": glyph(path((350, CAP), (250, CAP), (250, 390), (180, 390), (180, 250), (250, 250), (250, 0), (350, 0))),
    "|": glyph(path((C, -80), (C, 700))),
    "}": glyph(path((150, CAP), (250, CAP), (250, 390), (320, 390), (320, 250), (250, 250), (250, 0), (150, 0))),
    "~": glyph(path((90, 260), (90, 340), (210, 340), (210, 280), (290, 280), (290, 340), (410, 340), (410, 260))),
}


# Internal reusable geometry for composed letters and compatibility symbols.
COMPONENTS = {
    ".dotlessi": glyph(path((C, 0), (C, 330))),
    ".grave": glyph(path((280, 0), (210, 70))),
    ".acute": glyph(path((220, 0), (290, 70))),
    ".circumflex": glyph(path((175, 0), (C, 70)), path((C, 70), (325, 0))),
    ".tilde": glyph(path((150, 10), (205, 65)), path((205, 65), (295, 15)), path((295, 15), (350, 70))),
    ".dieresis": glyph(dots=((195, 35, 0.72), (305, 35, 0.72))),
    ".ring": glyph(ring(180, 320, 0, 90)),
    ".caron": glyph(path((175, 70), (C, 0)), path((C, 0), (325, 70))),
    ".cedilla": glyph(path((C, 0), (C, -65), (205, -110))),
    ".macron": glyph(path((160, 35), (340, 35))),
}


COMBINING_MARKS = {
    "\u0300": ".grave",
    "\u0301": ".acute",
    "\u0302": ".circumflex",
    "\u0303": ".tilde",
    "\u0308": ".dieresis",
    "\u030a": ".ring",
    "\u030c": ".caron",
    "\u0327": ".cedilla",
}


# Bespoke Latin letters: these share the global grid and stroke, but need
# their own joins instead of mechanically overlapping two finished glyphs.
GLYPHS.update({
    "µ": glyph(path((L, XH), (L, -120)), path((L, 0), (R, 0), (R, XH)), path((R, 0), (430, -100))),
    "Æ": combine(transform(GLYPHS["A"], 0.72, 1, 5, 0), transform(GLYPHS["E"], 0.68, 1, 165, 0)),
    "Ð": combine(GLYPHS["D"], glyph(path((55, MID), (265, MID)))),
    "Ø": combine(GLYPHS["O"], glyph(path((75, -25), (425, 665)))),
    "Þ": glyph(path((L, 0), (L, CAP)), path((L, 520), (R, 520), (R, 210), (L, 210))),
    "ß": glyph(path((L, 0), (L, CAP), (R, CAP), (R, MID), (C, MID)), path((C, MID), (R, MID), (R, 0), (C, 0))),
    "æ": combine(transform(GLYPHS["a"], 0.72, 1, -10, 0), transform(GLYPHS["e"], 0.68, 1, 165, 0)),
    "ð": combine(GLYPHS["o"], glyph(path((C, XH), (C, 610), (340, CAP)), path((155, 540), (345, 600)))),
    "ø": combine(GLYPHS["o"], glyph(path((80, -25), (420, 465)))),
    "þ": glyph(path((L, DESC), (L, CAP)), bowl(left=L, right=R, bottom=0, top=XH)),
    "ƒ": glyph(path((150, DESC), (185, -95), (310, 530), (350, CAP), (420, CAP)), path((90, XMID), (350, XMID))),
    "Œ": combine(transform(GLYPHS["O"], 0.70, 1, 0, 0), transform(GLYPHS["E"], 0.68, 1, 165, 0)),
    "œ": combine(transform(GLYPHS["o"], 0.70, 1, 0, 0), transform(GLYPHS["e"], 0.68, 1, 165, 0)),
})


# Direct symbols that benefit from the same primitives but are not letters.
GLYPHS.update({
    "¡": glyph(path((C, 0), (C, 420)), dots=((C, 595, 1.0),)),
    "¿": glyph(path((R, 50), (345, 0), (155, 0), (L, 50), (L, 190), (C, MID), (C, 420)), dots=((C, 595, 1.0),)),
    "¢": combine(glyph(c_shape(bottom=80, top=560)), glyph(path((C, -40), (C, CAP)))),
    "£": glyph(path((360, 590), (320, CAP), (210, CAP), (165, 590), (165, 80), (120, 0), (405, 0)), path((80, 300), (330, 300))),
    "¤": glyph(ring(155, 345, 180, 460), path((90, 540), (155, 460)), path((345, 180), (410, 100)), path((410, 540), (345, 460)), path((155, 180), (90, 100))),
    "¥": combine(GLYPHS["Y"], glyph(path((120, 230), (380, 230)), path((120, 120), (380, 120)))),
    "¦": glyph(path((C, -50), (C, 220)), path((C, 420), (C, 690))),
    "§": glyph(path((360, 590), (320, CAP), (170, CAP), (130, 590), (130, 450), (370, 190), (370, 50), (330, 0), (180, 0), (140, 50)), path((340, 480), (130, 250), (130, 140), (170, 90))),
    "¬": glyph(path((90, MID), (410, MID), (410, 150))),
    "¶": glyph(path((390, CAP), (180, CAP), (110,570), (110,390), (180, MID), (C, MID)), path((C, CAP), (C, 0)), path((360, CAP), (360, 0))),
    "×": glyph(path((110, 500), (390, 140)), path((390, 500), (110, 140))),
    "÷": glyph(path((100, MID), (400, MID)), dots=((C, 520, 0.82), (C, 120, 0.82))),
    "€": combine(glyph(c_shape(bottom=0, top=CAP)), glyph(path((80, 230), (340, 230)), path((80, 410), (340, 410)))),
    "°": glyph(ring(180, 320, 430, 590)),
    "±": glyph(path((C, 220), (C, 580)), path((80, 400), (420, 400)), path((80, 80), (420, 80))),
    "·": glyph(dots=((C, MID, 1.0),)),
    "«": glyph(path((260, 520), (90, MID), (260, 120)), path((410, 520), (240, MID), (410, 120))),
    "»": glyph(path((90, 520), (260, MID), (90, 120)), path((240, 520), (410, MID), (240, 120))),
    "‹": glyph(path((340, 520), (150, MID), (340, 120))),
    "›": glyph(path((160, 520), (350, MID), (160, 120))),
    "–": glyph(path((80, MID), (420, MID))),
    "—": glyph(path((20, MID), (480, MID))),
    "‘": glyph(path((280, CAP), (220, 560), (220, 470))),
    "’": glyph(path((220, 470), (280, 550), (280, CAP))),
    "‚": glyph(path((280, 100), (220, 20), (220, -70))),
    "“": glyph(path((210, CAP), (150, 560), (150, 470)), path((350, CAP), (290, 560), (290, 470))),
    "”": glyph(path((150, 470), (210, 550), (210, CAP)), path((290, 470), (350, 550), (350, CAP))),
    "„": glyph(path((210, 100), (150, 20), (150, -70)), path((350, 100), (290, 20), (290, -70))),
    "†": glyph(path((C, -20), (C, CAP)), path((90, 430), (410, 430))),
    "‡": glyph(path((C, -20), (C, CAP)), path((90, 450), (410, 450)), path((90, 170), (410, 170))),
    "•": glyph(dots=((C, MID, 1.8),)),
    "…": glyph(dots=((105, 45, 0.75), (C, 45, 0.75), (395, 45, 0.75))),
    "‰": glyph(ring(65, 165, 455, 595), path((105, 40), (395, 600)), ring(235, 335, 45, 185), ring(340, 440, 45, 185)),
})


IDENTITY = (1, 0, 0, 1, 0, 0)


def ref(name, xx=1, yy=1, dx=0, dy=0):
    return (name, (xx, 0, 0, yy, dx, dy))


# References scale completed glyphs, so small text also gets proportionally
# smaller strokes rather than cramped full-weight counters.
REFERENCES = {
    "\u00a0": (),
    "\u00ad": (ref("-"),),
    "©": (ref("O", 0.90, 0.90, 25, 30), ref("C", 0.38, 0.38, 155, 205)),
    "®": (ref("O", 0.90, 0.90, 25, 30), ref("R", 0.38, 0.38, 155, 205)),
    "ª": (ref("a", 0.55, 0.55, 112, 330),),
    "º": (ref("o", 0.55, 0.55, 112, 330),),
    "²": (ref("2", 0.55, 0.55, 112, 285),),
    "³": (ref("3", 0.55, 0.55, 112, 285),),
    "¹": (ref("1", 0.55, 0.55, 112, 285),),
    "¼": (ref("1", 0.42, 0.42, 35, 350), ref("/", 0.78, 0.78, 55, 70), ref("4", 0.42, 0.42, 260, -10)),
    "½": (ref("1", 0.42, 0.42, 35, 350), ref("/", 0.78, 0.78, 55, 70), ref("2", 0.42, 0.42, 260, -10)),
    "¾": (ref("3", 0.42, 0.42, 35, 350), ref("/", 0.78, 0.78, 55, 70), ref("4", 0.42, 0.42, 260, -10)),
    "™": (ref("T", 0.42, 0.42, 15, 360), ref("M", 0.42, 0.42, 270, 360)),
    "ˆ": (ref(".circumflex", dy=530),),
    "˜": (ref(".tilde", dy=530),),
    "¨": (ref(".dieresis", dy=530),),
    "¯": (ref(".macron", dy=530),),
    "´": (ref(".acute", dy=530),),
    "¸": (ref(".cedilla"),),
}


CP1252_EXTRA = "€‚ƒ„…†‡ˆ‰Š‹ŒŽ‘’“”•–—˜™š›œžŸ"
TARGET_CODEPOINTS = tuple(sorted({*range(0x20, 0x7F), *range(0xA0, 0x100), *map(ord, CP1252_EXTRA)}))


def decomposition(char):
    """Return (base, mark) for the supported canonical Latin composites."""
    parts = normalize("NFD", char)
    if len(parts) == 2 and parts[1] in COMBINING_MARKS and ord(parts[0]) < 0x80:
        return (".dotlessi" if parts[0] == "i" else parts[0], COMBINING_MARKS[parts[1]])
    return None


assert len(TARGET_CODEPOINTS) == 218
assert set(map(chr, range(0x20, 0x7F))) <= GLYPHS.keys()
